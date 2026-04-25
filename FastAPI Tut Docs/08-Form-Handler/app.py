from fastapi import FastAPI, Form, Request,Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from db import create_db_and_tables,SessionLocal,LogUser
import uvicorn
from pydantic import BaseModel
from sqlalchemy.orm import Session

class LogUserModel(BaseModel):
    username: str
    email: str
    

create_db_and_tables()  # Create database tables on startup

def get_db():
    """Dependency: Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"name": "FastAPI Form Handling"}
    )


@app.post("/submit/")
async def submit_form(request: Request, username: str = Form(...), email: str = Form(...), db: Session = Depends(get_db)):
    # Save to database
    log_user = LogUser(username=username, email=email)
    db.add(log_user)
    db.commit()
    db.refresh(log_user)
    return templates.TemplateResponse(
        request=request,
        name="output.html",
        context={"username": username, "email": email}
    )
