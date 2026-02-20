from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import text
from database import engine
from passlib.context import CryptContext
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon demo (allow all)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===============================
# ROOT
# ===============================
@app.get("/")
def home():
    return {
        "message": "Sleep Apnea Backend is running",
        "available_endpoints": {
            "Register": "/register",
            "Login": "/login",
            "Doctor - View Patients": "/doctor/patients",
            "Doctor - View Patient Report": "/doctor/patient/{patient_id}",
            "Doctor - Analyze File": "/doctor/analyze/{patient_id}",
            "Doctor - Review": "/doctor/review/{session_id}",
            "Patient - View Results": "/patient/results/{user_id}",
            "Swagger Docs": "/docs"
        }
    }


# ===============================
# MODELS
# ===============================

class UserRegister(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


# ===============================
# REGISTER (PATIENT ONLY)
# ===============================
@app.post("/register")
def register(user: UserRegister):

    hashed_password = pwd_context.hash(user.password)

    with engine.connect() as connection:

        # Insert into users
        result = connection.execute(
            text("""
                INSERT INTO users (name, email, password, role)
                VALUES (:name, :email, :password, 'patient')
                RETURNING id
            """),
            {
                "name": user.name,
                "email": user.email,
                "password": hashed_password
            }
        )

        user_id = result.fetchone()[0]

        # Insert into patients (linked to user)
        connection.execute(
            text("""
                INSERT INTO patients (name, email, user_id)
                VALUES (:name, :email, :user_id)
            """),
            {
                "name": user.name,
                "email": user.email,
                "user_id": user_id
            }
        )

        connection.commit()

    return {"message": "Patient registered successfully"}


# ===============================
# LOGIN
# ===============================
@app.post("/login")
def login(user: UserLogin):
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT id, name, password, role FROM users WHERE email = :email"),
            {"email": user.email}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        user_id, name, stored_password, role = result

        if not pwd_context.verify(user.password, stored_password):
            raise HTTPException(status_code=401, detail="Invalid password")

        connection.execute(
            text("INSERT INTO login_logs (user_id) VALUES (:user_id)"),
            {"user_id": user_id}
        )

        connection.commit()

    return {
        "message": "Login successful",
        "user_id": user_id,
        "name": name,        # ✅ ADDED
        "role": role
    }



# ===============================
# DOCTOR - VIEW ALL PATIENTS
# ===============================
@app.get("/doctor/patients")
def get_all_patients():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT 
                    p.id,
                    p.name,
                    p.email,
                    p.gender,
                    p.phone_number,
                    p.created_at
                FROM patients p
                JOIN users u ON p.user_id = u.id
                WHERE u.role = 'patient'
                ORDER BY p.id DESC
            """)
        )

        return [dict(row._mapping) for row in result.fetchall()]
    
    

# ===============================
# DOCTOR - VIEW PATIENT REPORT
# ===============================
@app.get("/doctor/patient/{patient_id}")
def get_patient_report(patient_id: int):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT 
                    p.id AS patient_id,
                    p.name,
                    p.email,
                    s.id AS session_id,
                    s.session_date,
                    m.heart_rate,
                    m.hrv,
                    m.spo2,
                    m.sleep_stage,
                    m.severity AS ai_severity,
                    m.ahi,
                    m.total_events,
                    m.confirmed_severity,
                    m.doctor_notes
                FROM patients p
                JOIN sleep_sessions s ON p.id = s.patient_id
                JOIN sleep_metrics m ON s.id = m.session_id
                WHERE p.id = :patient_id
                ORDER BY s.session_date DESC
            """),
            {"patient_id": patient_id}
        )

        return [dict(row._mapping) for row in result.fetchall()]


# ===============================
# DOCTOR - ANALYZE FILE
# ===============================
@app.post("/doctor/analyze/{patient_id}")
async def analyze_file(patient_id: int, files: list[UploadFile] = File(...)):

    # Verify patient exists
    with engine.connect() as connection:
        patient = connection.execute(
            text("SELECT id FROM patients WHERE id = :id"),
            {"id": patient_id}
        ).fetchone()

        if not patient:
            return {"error": "Patient not found"}

    multipart_files = []
    for file in files:
        content = await file.read()
        multipart_files.append(
            ("files", (file.filename, content, file.content_type))
        )

    ai_response = requests.post(
        "http://127.0.0.1:8001/upload",
        files=multipart_files
    )

    if ai_response.status_code != 200:
        return {"error": ai_response.text}

    result = ai_response.json()

    with engine.connect() as connection:

        # Create session
        session_result = connection.execute(
            text("""
                INSERT INTO sleep_sessions (patient_id)
                VALUES (:patient_id)
                RETURNING id
            """),
            {"patient_id": patient_id}
        )

        session_id = session_result.fetchone()[0]

        # Store AI results
        connection.execute(
            text("""
                INSERT INTO sleep_metrics
                (session_id, heart_rate, hrv, spo2, sleep_stage,
                 severity, ahi, total_events)
                VALUES
                (:session_id, :heart_rate, :hrv, :spo2, :sleep_stage,
                 :severity, :ahi, :total_events)
            """),
            {
                "session_id": session_id,
                "heart_rate": result["heart_rate"],
                "hrv": result["hrv"],
                "spo2": result["spo2"],
                "sleep_stage": result["sleep_stage"],
                "severity": result["severity"],
                "ahi": result["ahi"],
                "total_events": result["total_events"]
            }
        )

        connection.commit()

    return {
        "message": "AI Analysis Stored",
        "session_id": session_id
    }


# ===============================
# DOCTOR - REVIEW SESSION
# ===============================
@app.post("/doctor/review/{session_id}")
def doctor_review(session_id: int, doctor_id: int,
                  notes: str, confirmed_severity: str):

    with engine.connect() as connection:

        # Verify doctor role
        doctor = connection.execute(
            text("SELECT role FROM users WHERE id = :id"),
            {"id": doctor_id}
        ).fetchone()

        if not doctor or doctor[0] != "doctor":
            return {"error": "Only doctors can review"}

        connection.execute(
            text("""
                UPDATE sleep_metrics
                SET doctor_notes = :notes,
                    confirmed_severity = :confirmed_severity,
                    reviewed_by = :doctor_id
                WHERE session_id = :session_id
            """),
            {
                "notes": notes,
                "confirmed_severity": confirmed_severity,
                "doctor_id": doctor_id,
                "session_id": session_id
            }
        )

        connection.commit()

    return {"message": "Review saved successfully"}


# ===============================
# PATIENT - VIEW OWN RESULTS
# ===============================
@app.get("/patient/results/{user_id}")
def get_patient_results(user_id: int):
    with engine.connect() as connection:

        # Get linked patient record
        patient = connection.execute(
            text("SELECT id FROM patients WHERE user_id = :uid"),
            {"uid": user_id}
        ).fetchone()

        if not patient:
            return {"error": "No patient record found"}

        patient_id = patient[0]

        result = connection.execute(
            text("""
                SELECT 
                    s.session_date,
                    m.heart_rate,
                    m.hrv,
                    m.spo2,
                    m.sleep_stage,
                    m.severity AS ai_severity,
                    m.confirmed_severity,
                    m.doctor_notes
                FROM sleep_sessions s
                JOIN sleep_metrics m ON s.id = m.session_id
                WHERE s.patient_id = :patient_id
                ORDER BY s.session_date DESC
            """),
            {"patient_id": patient_id}
        )

        return [dict(row._mapping) for row in result.fetchall()]
