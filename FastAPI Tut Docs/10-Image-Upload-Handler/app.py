from fastapi import FastAPI, Form, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import shutil

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Use the same path for both saving and retrieving
UPLOAD_FOLDER = "static/uploads/"  # File system path for saving
UPLOAD_URL = "/static/uploads/"     # URL path for browser display


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"name": "FastAPI Image Handling"}
    )


@app.post("/submit/")
async def submit_form(request: Request, username: str = Form(...), email: str = Form(...), file: UploadFile = File(...)):
    # Save file to disk
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Build URL to display in browser
    filename = file.filename
    image_path = f"{UPLOAD_URL}{filename}"
    print(f"Username: {username}, Email: {email}, Image Path: {image_path}")
    return templates.TemplateResponse(
        request=request,
        name="output.html",
        context={"username": username,
                 "email": email, "image_path": image_path}
    )
