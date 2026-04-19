import os
from fastapi import FastAPI, UploadFile, File

from typing import List
app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create directory if doesn't exist

@app.post("/upload/")
def upload_file(file: UploadFile = File(...)):
    with open("uploads/" + file.filename, "wb") as f:
        f.write(file.file.read())
    return {"message": "File saved"}



@app.post("/upload-multiple")
def upload_multiple_files(files:List[UploadFile]=File(...)):
    uploads=[]
    for file in files:
        file_path=os.path.join(UPLOAD_DIR,file.filename)
        with open(file_path,"wb") as f:
            f.write(file.file.read())
        uploads.append(file.filename)
    return {"message": "Files saved", "files": uploads}

