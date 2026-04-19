from fastapi import FastAPI, Form, Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import secrets
from auth_utils import (hash_password, verify_password)


from db_model import User, SessionLocal, engine, Base, UserCreate

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Replace with your actual n8n webhook URL
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/1e73106a-b0c7-4f02-b128-62ddc524fe55"


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chatbot.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username or email already exists"}
        )

    # Generate API key
    api_key = secrets.token_urlsafe(32)
    hashed_pwd = hash_password(password)

    # Create user
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_pwd,
        api_key=api_key
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return templates.TemplateResponse(
        "register_success.html",
        {"request": request, "api_key": api_key, "username": username}
    )


@app.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == username).first()

    if not db_user or not verify_password(password, db_user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    # Return login success page with API key to store
    return templates.TemplateResponse(
        "login_success.html",
        {"request": request, "api_key": db_user.api_key, "username": username}
    )


@app.post("/chat", response_class=HTMLResponse)
async def handle_chatbot(
    request: Request,
    user_input: str = Form(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validate API key
    db_user = db.query(User).filter(User.api_key == api_key).first()

    if not db_user:
        return templates.TemplateResponse(
            "chatbot.html",
            {"request": request, "error": "Invalid API key. Please login first.",
                "api_key": api_key}
        )

    print(f"User: {db_user.username} | Input: {user_input}")

    # Send request to n8n webhook
    async with httpx.AsyncClient() as client:
        response = await client.get(
            N8N_WEBHOOK_URL,
            params={"username": db_user.username, "messaage": user_input}
        )
        ai_response = response.json().get("ai", "No response from AI")

    return templates.TemplateResponse(
        "chatbot.html",
        {"request": request, "response": ai_response, "api_key": api_key}
    )
