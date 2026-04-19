from fastapi import FastAPI, Form, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import shutil

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "static/uploads/"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # file name, arguments in dict form
    return templates.TemplateResponse("index.html", {"request": request, "name": "FastAPI Image Handling"})


@app.post("/submit/")
async def submit_form(request: Request, username: str = Form(...), email: str = Form(...), file: UploadFile = File(...)):
    # Process the form data
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_location, "wb") as buffer:  # store the file in the path
        shutil.copyfileobj(file.file, buffer)

    # send the file location to the html form again
    filename = file.filename
    image_path = f"{UPLOAD_FOLDER}{filename}"
    print(f"Username: {username}, Email: {email}, Image Path: {image_path}")
    return templates.TemplateResponse("output.html", {"request": request, "username": username, "email": email, "image_path": image_path})
