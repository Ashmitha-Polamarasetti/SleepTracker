from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import text
from passlib.context import CryptContext
from database import engine
from typing import List
import requests
from fastapi.responses import FileResponse

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==============================
# MODELS
# ==============================

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: str
    password: str

class ProfileUpdate(BaseModel):
    gender: str
    phone_number: str

class DoctorReview(BaseModel):
    session_id: int
    confirmed_severity: str
    doctor_notes: str


# ==============================
# REGISTER
# ==============================

@app.post("/register")
def register(user: UserRegister):

    hashed_password = pwd_context.hash(user.password)

    with engine.connect() as conn:

        result = conn.execute(
            text("""
                INSERT INTO users (name, email, password, role)
                VALUES (:name, :email, :password, :role)
                RETURNING id
            """),
            {
                "name": user.name,
                "email": user.email,
                "password": hashed_password,
                "role": user.role
            }
        )

        user_id = result.fetchone()[0]

        if user.role == "patient":
            conn.execute(
                text("INSERT INTO patients (user_id) VALUES (:uid)"),
                {"uid": user_id}
            )

        conn.commit()

    return {"message": "User registered successfully"}


# ==============================
# LOGIN
# ==============================

@app.post("/login")
def login(user: UserLogin):

    with engine.connect() as conn:

        result = conn.execute(
            text("SELECT id, name, password, role FROM users WHERE email=:email"),
            {"email": user.email}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        user_id, name, stored_password, role = result

        if not pwd_context.verify(user.password, stored_password):
            raise HTTPException(status_code=401, detail="Invalid password")

    return {"user_id": user_id, "name": name, "role": role}


# ==============================
# GET PATIENTS
# ==============================

@app.get("/doctor/patients")
def get_patients():

    with engine.connect() as conn:

        result = conn.execute(text("""
            SELECT u.id AS user_id, u.name, p.gender, p.phone_number
            FROM users u
            JOIN patients p ON u.id = p.user_id
            WHERE u.role='patient'
        """))

        return [dict(row._mapping) for row in result.fetchall()]


# ==============================
# UPLOAD + SAVE + RETURN AI DATA
# ==============================

@app.post("/doctor/upload-and-save")
async def upload_and_save(user_id: int, files: List[UploadFile] = File(...)):

    if len(files) != 3:
        raise HTTPException(status_code=400, detail="Upload exactly 3 files")

    files_data = [
        ("files", (file.filename, await file.read(), file.content_type))
        for file in files
    ]

    ai_response = requests.post(
        "http://sleep_ai:8001/upload",
        files=files_data
    )

    if ai_response.status_code != 200:
        raise HTTPException(status_code=500, detail="AI prediction failed")

    ai_data = ai_response.json()

    with engine.connect() as conn:

        patient = conn.execute(
            text("SELECT id FROM patients WHERE user_id=:uid"),
            {"uid": user_id}
        ).fetchone()

        patient_id = patient[0]

        session = conn.execute(
            text("""
                INSERT INTO sleep_sessions (patient_id)
                VALUES (:pid)
                RETURNING id
            """),
            {"pid": patient_id}
        )

        session_id = session.fetchone()[0]

        conn.execute(
            text("""
                INSERT INTO sleep_metrics (
                    session_id,
                    heart_rate,
                    hrv,
                    spo2,
                    sleep_stage,
                    ahi,
                    total_events,
                    ai_severity
                )
                VALUES (
                    :sid, :hr, :hrv, :spo2, :stage, :ahi, :events, :severity
                )
            """),
            {
                "sid": session_id,
                "hr": ai_data["heart_rate"],
                "hrv": ai_data["hrv"],
                "spo2": ai_data["spo2"],
                "stage": ai_data["sleep_stage"],
                "ahi": ai_data["ahi"],
                "events": ai_data["total_events"],
                "severity": ai_data["severity"]
            }
        )

        conn.commit()

    # 🔥 IMPORTANT: RETURN AI DATA + session_id
    return {
        "session_id": session_id,
        "heart_rate": ai_data["heart_rate"],
        "hrv": ai_data["hrv"],
        "spo2": ai_data["spo2"],
        "sleep_stage": ai_data["sleep_stage"],
        "ahi": ai_data["ahi"],
        "total_events": ai_data["total_events"],
        "severity": ai_data["severity"]
    }


# ==============================
# DOCTOR REVIEW
# ==============================

@app.put("/doctor/review")
def doctor_review(data: DoctorReview):

    with engine.connect() as conn:

        conn.execute(
            text("""
                UPDATE sleep_metrics
                SET confirmed_severity=:severity,
                    doctor_notes=:notes
                WHERE session_id=:sid
            """),
            {
                "severity": data.confirmed_severity,
                "notes": data.doctor_notes,
                "sid": data.session_id
            }
        )

        conn.commit()

    return {"message": "Review saved"}


# ==============================
# GET PATIENT REPORTS
# ==============================

@app.get("/patient/reports/{user_id}")
def patient_reports(user_id: int):

    with engine.connect() as conn:

        patient = conn.execute(
            text("SELECT id FROM patients WHERE user_id=:uid"),
            {"uid": user_id}
        ).fetchone()

        patient_id = patient[0]

        result = conn.execute(text("""
            SELECT s.id as session_id,
                   s.session_date,
                   m.heart_rate,
                   m.hrv,
                   m.spo2,
                   m.sleep_stage,
                   m.ahi,
                   m.total_events,
                   m.ai_severity,
                   m.confirmed_severity,
                   m.doctor_notes
            FROM sleep_sessions s
            JOIN sleep_metrics m ON s.id = m.session_id
            WHERE s.patient_id=:pid
            ORDER BY s.session_date DESC
        """), {"pid": patient_id})

        return [dict(row._mapping) for row in result.fetchall()]


# ==============================
# PROFILE UPDATE
# ==============================

@app.put("/patient/profile/{user_id}")
def update_profile(user_id: int, data: ProfileUpdate):

    with engine.connect() as conn:

        conn.execute(
            text("""
                UPDATE patients
                SET gender=:gender,
                    phone_number=:phone
                WHERE user_id=:uid
            """),
            {
                "gender": data.gender,
                "phone": data.phone_number,
                "uid": user_id
            }
        )

        conn.commit()

    return {"message": "Profile updated"}


@app.get("/")
def root():
    return FileResponse("frontend/index.html")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")