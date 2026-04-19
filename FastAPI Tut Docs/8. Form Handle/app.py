from fastapi import FastAPI, Form, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # file name, arguments in dict form
    return templates.TemplateResponse("index.html", {"request": request, "name": "FastAPI Form Handling"})


@app.post("/submit/")
async def submit_form(request: Request, username: str = Form(...), email: str = Form(...)):
    # Process the form data
    print(f"Username: {username}, Email: {email}")
    return templates.TemplateResponse("output.html", {"request": request, "username": username, "email": email})
