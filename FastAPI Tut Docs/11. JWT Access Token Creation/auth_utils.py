from passlib.context import CryptContext
from datetime import date, datetime, timedelta, timezone
from jose import jwt, JWTError  # requires 'python-jose', 'jose' package

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "ThisIsASecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str):
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return password_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES) if expires_delta is None else expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
                                           if expires_delta is None else expires_delta)
    #  expire = current time + default expire time if custom expire time not mentiod else the custom expire tim
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
# decode_access_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpc2ZhciIsImV4cCI6MTc2ODE0NjczNX0.SMms7QMFYZhLCgtWoemFj1Lzj4FsQL5WNSAm58QwosY")
