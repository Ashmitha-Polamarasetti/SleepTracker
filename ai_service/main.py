from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
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
async def upload_files(files: List[UploadFile] = File(...)):

    if len(files) != 3:
        raise HTTPException(status_code=400, detail="Upload exactly 3 files: .dat, .hea, .apn")

    base_name = None

    for file in files:

        if not file.filename.endswith((".dat", ".hea", ".apn")):
            raise HTTPException(status_code=400, detail="Invalid file type")

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        name_without_ext = file.filename.split('.')[0]

        if base_name is None:
            base_name = name_without_ext
        elif base_name != name_without_ext:
            raise HTTPException(status_code=400, detail="All files must share same base name")

    result = predict_psg(base_name)

    return JSONResponse(content=result)
