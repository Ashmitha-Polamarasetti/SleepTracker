from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os

from ai_model.inference import predict_psg

app = FastAPI()

UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Sleep Apnea AI Service Running"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Remove extension (.dat/.edf) if present
    record_name = file.filename.split('.')[0]

    # Run AI prediction
    result = predict_psg(record_name)

    return JSONResponse(content=result)

