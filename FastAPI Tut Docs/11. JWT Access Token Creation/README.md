# JWT Access Token Creation - Detailed, Code-Aligned Tutorial

## Overview

This tutorial is based on the exact code currently present in this folder.

Goal of this project:

1. Register users with hashed passwords.
2. Login users and issue two JWTs:
   - access token (short life, currently 1 minute)
   - refresh token (long life, currently 7 days)
3. Protect an endpoint using bearer access token.
4. Generate a new access token from refresh token.

---

## Project Files and Their Roles

```text
11. JWT Access Token Creation/
|-- app.py
|-- auth_utils.py
|-- database.py
|-- models.py
|-- jwt_client.js
|-- database.db
`-- README.md
```

1. `database.py`: DB connection, SQLAlchemy base, session factory.
2. `models.py`: `User` table schema.
3. `auth_utils.py`: password hash/verify + JWT create/decode helpers.
4. `app.py`: API endpoints (`/register`, `/login`, `/refresh`, `/protected`).
5. `jwt_client.js`: sample frontend flow for storing tokens and auto-refresh.

---

## End-to-End Flow (Big Picture)

1. Register:
   - create user row with hashed password.
2. Login:
   - verify password,
   - issue access token + refresh token.
3. Protected call:
   - send `Authorization: Bearer <access_token>`.
4. Access token expires:
   - call `/refresh` with refresh token,
   - get new access token,
   - retry protected request.

---

## File-by-File, Line-by-Line Explanation

## 1) `database.py`

Current code:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

DATABASE_URL = "sqlite:///./database.db"

engine= create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal= sessionmaker(autoflush=False, bind=engine)
```

Line-by-line explanation:

1. `from sqlalchemy import create_engine`
   - imports SQLAlchemy engine creator.
2. `from sqlalchemy.ext.declarative import declarative_base`
   - imports base class factory for ORM models.
3. `from sqlalchemy.orm import sessionmaker`
   - imports session factory utility.
4. `Base = declarative_base()`
   - creates shared base class used by ORM models.
5. `DATABASE_URL = "sqlite:///./database.db"`
   - sets SQLite file path.
6. `engine= create_engine(...)`
   - creates DB engine.
   - `check_same_thread=False` is needed for SQLite with FastAPI request handling.
7. `SessionLocal= sessionmaker(...)`
   - builds session factory used per request.
   - `autoflush=False` means SQLAlchemy will not auto-flush before each query.

---

## 2) `models.py`

Current code:

```python
from database import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)
```

Line-by-line explanation:

1. `from database import Base`
   - imports shared SQLAlchemy base class.
2. `from sqlalchemy import Column, Integer, String`
   - imports column and SQL types.
3. `class User(Base):`
   - creates ORM model class mapped to a table.
4. `__tablename__ = "users"`
   - table name is `users`.
5. `id = Column(Integer, primary_key=True, index=True)`
   - integer PK with index.
6. `username = Column(String, unique=True, index=True)`
   - unique username with index for faster lookup.
7. `password = Column(String)`
   - stores hashed password text.
8. `email = Column(String, unique=True, index=True)`
   - unique email with index.

---

## 3) `auth_utils.py`

Current code (key parts):

```python
from passlib.context import CryptContext
from datetime import date, datetime, timedelta, timezone
from jose import jwt, JWTError

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "ThisIsASecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

Line-by-line explanation:

1. `from passlib.context import CryptContext`
   - password hash/verify helper from passlib.
2. `from datetime import date, datetime, timedelta, timezone`
   - datetime tools for expiry timestamps.
   - note: `date` is imported but currently not used.
3. `from jose import jwt, JWTError`
   - JWT encode/decode and exception handling.
4. `password_context = CryptContext(...)`
   - configures bcrypt password hashing.
5. `SECRET_KEY = "ThisIsASecret"`
   - signing key for JWT (learning only; use env var in production).
6. `ALGORITHM = "HS256"`
   - JWT signing algorithm.
7. `ACCESS_TOKEN_EXPIRE_MINUTES = 1`
   - current access token lifetime.
8. `REFRESH_TOKEN_EXPIRE_DAYS = 7`
   - current refresh token lifetime.

### Password helpers

```python
def hash_password(password: str):
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return password_context.verify(plain_password, hashed_password)
```

- `hash_password`: one-way hashes user password.
- `verify_password`: checks plain password against stored hash.

### Access token creation

```python
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES) if expires_delta is None else expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

Line-by-line:

1. copies incoming payload to avoid mutating original.
2. computes expiry:
   - default: now + 1 minute,
   - or uses provided `expires_delta`.
3. adds `exp` claim.
4. signs token with secret + algorithm.
5. returns token string.

### Refresh token creation

`create_refresh_token(...)` is same pattern, but expiry is now + 7 days by default.

### Decode helpers

```python
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

- decodes and validates signature + expiry.
- returns payload dict if valid.
- returns `None` when invalid/expired.

`decode_refresh_token` uses same pattern.

---

## 4) `app.py`

Current code:

```python
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

Base.metadata.create_all(bind=engine)
security = HTTPBearer()
```

Line-by-line (setup section):

1. `FastAPI, Depends, HTTPException, Header` imported from FastAPI.
   - note: `Header` is imported but currently unused.
2. `HTTPBearer, HTTPAuthorizationCredentials` imports security utilities.
3. `Session` imports SQLAlchemy session type.
4. imports DB setup (`SessionLocal`, `engine`, `Base`).
5. imports Pydantic `BaseModel`.
6. imports `User` model.
7. imports auth helper functions.
8. `app = FastAPI()` creates the API app.
9. `Base.metadata.create_all(bind=engine)` creates DB tables if missing.
10. `security = HTTPBearer()` sets bearer-token dependency extractor.

### DB dependency function

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Line-by-line:

1. opens DB session.
2. yields session to route handler.
3. always closes session in `finally`.

### Request body models

```python
class UserCreate(BaseModel):
    username: str
    password: str
    email: str


class UserLogin(BaseModel):
    username: str
    password: str
```

- `UserCreate` validates `/register` body.
- `UserLogin` validates `/login` body.

### `/register` endpoint

```python
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
```

Line-by-line:

1. route decorator maps POST `/register`.
2. receives validated `user` body and injected DB session.
3. creates `User` object.
4. hashes password before storing.
5. adds row to session.
6. commits transaction.
7. refreshes object from DB.
8. returns success response.

### `/login` endpoint

```python
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": db_user.username})
    refresh_token = create_refresh_token(data={"sub": db_user.username})
    return {"access_token": access_token, "refresh_token": refresh_token}
```

Line-by-line:

1. route decorator maps POST `/login`.
2. queries first user with matching username.
3. validates user existence + password hash check.
4. raises `400` on invalid credentials.
5. creates access token with `sub` claim = username.
6. creates refresh token with same `sub`.
7. returns both tokens.

### `/refresh` endpoint

```python
@app.post("/refresh")
def refresh_token_endpoint(refresh_token: str):
    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    new_access_token = create_access_token(data={"sub": payload["sub"]})
    return {"access_token": new_access_token}
```

Line-by-line:

1. route decorator maps POST `/refresh`.
2. receives `refresh_token` as scalar parameter.
   - in FastAPI this means query parameter by default (unless explicitly Body/Form).
3. decodes/validates refresh token.
4. returns `401` if invalid/expired.
5. issues new access token using same subject.
6. returns new access token.

### `/protected` endpoint

```python
@app.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"msg": f"Hello, {payload['sub']}! This is a protected route."}
```

Line-by-line:

1. route decorator maps GET `/protected`.
2. `Depends(security)` extracts bearer token from header.
3. reads raw token string.
4. decodes/validates access token.
5. returns `401` if invalid/expired.
6. returns protected message with `sub` value.

---

## 5) `jwt_client.js` Note (Important)

Current JS refresh call sends JSON body:

```javascript
body: JSON.stringify({ refresh_token: refreshToken });
```

But backend expects scalar `refresh_token` parameter (query style by default).

To match current backend exactly, call refresh like:

```text
POST /refresh?refresh_token=<your_refresh_token>
```

Or update backend later to accept JSON body with Pydantic model.

---

## 6) Exact API Usage (As Code Currently Works)

### Register

`POST /register`

```json
{
  "username": "alice",
  "password": "pass123",
  "email": "alice@example.com"
}
```

### Login

`POST /login`

```json
{
  "username": "alice",
  "password": "pass123"
}
```

Returns:

```json
{
  "access_token": "<access_jwt>",
  "refresh_token": "<refresh_jwt>"
}
```

### Protected route

`GET /protected`

Header:

```text
Authorization: Bearer <access_jwt>
```

### Refresh route (current code shape)

`POST /refresh?refresh_token=<refresh_jwt>`

Returns:

```json
{
  "access_token": "<new_access_jwt>"
}
```

---

## 7) Run Instructions

Install dependencies:

```bash
pip install fastapi uvicorn sqlalchemy python-jose[cryptography] passlib[bcrypt]
```

Run server:

```bash
uvicorn app:app --reload
```

Open docs:

```text
http://127.0.0.1:8000/docs
```

Testing order:

1. `/register`
2. `/login`
3. `/protected` with access token
4. wait > 1 minute (access token expires)
5. `/refresh` with refresh token
6. `/protected` with new access token

---

## 8) Security Notes (Current vs Production)

Current code is good for learning but improve before production:

1. move `SECRET_KEY` to environment variable,
2. avoid hardcoded secret values,
3. add duplicate check for username/email before insert,
4. consider stronger validation rules,
5. use HTTPS,
6. consider refresh token revocation strategy.

---

## 9) Key Concept Summary

1. Access token is short-lived and used for protected endpoints.
2. Refresh token is long-lived and used to issue new access tokens.
3. Passwords are hashed before DB storage.
4. Protected endpoint uses bearer header extraction + token decode.
5. DB session lifecycle is managed per request via `get_db()`.
