from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from pydantic import BaseModel
from models import User
from auth_utils import (
    hash_password, create_access_token, decode_access_token, verify_password,
    create_refresh_token, decode_refresh_token
)

app = FastAPI()

# Create the database tables
Base.metadata.create_all(bind=engine)
security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserCreate(BaseModel):
    username: str
    password: str
    email: str


class UserLogin(BaseModel):
    username: str
    password: str


@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        username=user.username,
        password=hash_password(user.password),
        email=user.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "User created successfully"}



# Issue both access and refresh tokens at login
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": db_user.username})
    refresh_token = create_refresh_token(data={"sub": db_user.username})
    return {"access_token": access_token, "refresh_token": refresh_token}


# Endpoint to refresh access token using refresh token
@app.post("/refresh")
def refresh_token_endpoint(refresh_token: str):
    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    new_access_token = create_access_token(data={"sub": payload["sub"]})
    return {"access_token": new_access_token}


@app.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"msg": f"Hello, {payload['sub']}! This is a protected route."}


'''
JWT Standard Claims:

sub - Subject (who the token is about)
exp - Expiration time (when token expires)
iat - Issued at (when token was created)
iss - Issuer (who created the token)
aud - Audience (who the token is for)
'''
