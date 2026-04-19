from passlib.context import CryptContext
from datetime import date, datetime, timedelta, timezone
from jose import jwt, JWTError  # requires 'python-jose', 'jose' package

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return password_context.verify(plain_password, hashed_password)
