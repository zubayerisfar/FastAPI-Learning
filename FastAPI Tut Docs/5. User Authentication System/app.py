from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from passlib.context import CryptContext
from db import engine, SessionLocal, Base
from models import User
from schema import Register, Login

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/register")
async def register(user: Register, db: Session = Depends(get_db)):
    query = select(User).where(User.username == user.username)
    existing_user = db.execute(query).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username Already Exists")
    hashed_password = password_context.hash(user.password)
    user = User(username=user.username, age=user.age, password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully!"}


@app.post("/login")
async def login(user: Login, db: Session = Depends(get_db)):
    query = select(User).where(User.username == user.username)
    # returns the list of matched user objects
    existing_user = db.query(User).filter(User.username == user.username).first()
    if not existing_user:
        raise HTTPException(
            status_code=400, detail="Invalid Username or Password")

    is_valid = password_context.verify(
        user.password, existing_user.password)
    if not is_valid:
        raise HTTPException(
            status_code=400, detail="Invalid Username or Password")

    return {"message": "Login successful!", "username": existing_user.username}

@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user