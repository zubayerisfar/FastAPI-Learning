# JWT Access Token & Refresh Token System - Complete Tutorial

## Overview

A complete authentication system where users register, login to get tokens, and access protected routes.

---

# PART 1: UNDERSTANDING THE DATABASE MODEL

## Step 1: Create the User Model (`models.py`)

First, we define what data gets stored in the database using SQLAlchemy ORM:

```python
from database import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # Stores Argon2 hash (NOT plain text)
    email = Column(String, unique=True, index=True)
```

**Line-by-Line Explanation:**

1. `from database import Base`
   - Import the base class that connects models to database tables

2. `from sqlalchemy import Column, Integer, String`
   - Import column types for defining table fields

3. `class User(Base):`
   - Create a User model class that inherits from Base
   - Automatically creates a database table

4. `__tablename__ = "users"`
   - The actual SQL table name will be `users`

5. `id = Column(Integer, primary_key=True, index=True)`
   - **Primary Key**: Unique identifier for each user (auto-increments)
   - **index=True**: Creates database index for faster lookups

6. `username = Column(String, unique=True, index=True)`
   - **unique=True**: No two users can have same username
   - **index=True**: Fast lookups by username

7. `password = Column(String)`
   - Stores **Argon2 hashed password** (not plain text for security)

8. `email = Column(String, unique=True, index=True)`
   - **unique=True**: No duplicate emails
   - **index=True**: Fast email lookups

**Database Table Created:**

```
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL
);
```

**Example Data in Database:**

```
| id | username  | password (hashed)              | email               |
|----|-----------|--------------------------------|---------------------|
| 1  | testuser  | $argon2id$v=19$m=65536$t=  ... |  testuser@gmail.com |
```

---

# PART 2: RUNNING THE APPLICATION

## Step 1: Install Dependencies

```bash
pip install fastapi uvicorn sqlalchemy argon2-cffi python-jose[cryptography]
```

## Step 2: Start the FastAPI Server

Navigate to the project folder and run:

```bash
uvicorn app:app --reload
```

**Console Output:**

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**What `--reload` does:**

- Automatically restarts server when you change code
- Great for development (remove in production)

## Step 3: Database Auto-Creation

When the app starts, this line in `app.py` executes:

```python
Base.metadata.create_all(bind=engine)
```

**What happens:**

- Checks if `database.db` file exists
- If not, creates it automatically
- Creates the `users` table automatically
- **No manual database setup needed!**

---

# PART 3: DATABASE MODELS SCREENSHOT

**Visual Output - File Structure:**

![Database Folder View](images/db_folder_view.png)

After running `uvicorn app:app --reload`, you'll see:

- `database.db` file created in your project folder
- This is a SQLite database file
- Contains the `users` table defined in `models.py`

**What's Inside database.db:**

```
database.db
└── users table
    ├── id (auto-increment)
    ├── username (unique)
    ├── password (argon2 hash)
    └── email (unique)
```

---

# PART 4: SWAGGER UI - INTERACTIVE DOCUMENTATION

## Open the Docs URL

Open your browser and go to:

```
http://127.0.0.1:8000/docs
```

**Visual Output - Swagger UI:**

![Swagger URL](images/swagger_url.png)

**What You See:**

- All API endpoints organized in sections
- Interactive testing interface (Try it out!)
- Green "Authorize" button (top-right)
- Each endpoint can be expanded to show details
- Default request/response examples

**Available Endpoints:**

- `POST /register` - Create new user account
- `POST /login` - Get access & refresh tokens
- `POST /refresh` - Get new access token when expired
- `GET /users` - Get all users (protected)
- `GET /users/{user_id}` - Get specific user (protected)

---

# PART 5: USER REGISTRATION

## Understanding the Registration Code

```python
# In app.py
class UserCreate(BaseModel):
    username: str = "testuser"
    password: str = "testpassword"
    email: str = "testuser@gmail.com"

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Hash the password using Argon2
    db_user = User(
        username=user.username,
        password=hash_password(user.password),  # ← Argon2 hashing
        email=user.email
    )

    # 2. Add to database
    db.add(db_user)
    db.commit()           # Save to database
    db.refresh(db_user)   # Reload from database

    return {"msg": "User created successfully"}
```

**Code Explanation:**

1. `UserCreate` - Pydantic model that validates request body
2. `hash_password()` - One-way encryption using Argon2
3. `db.add()` - Prepare the record for saving
4. `db.commit()` - Actually save to database
5. `db.refresh()` - Reload from database to get default values

**Password Hashing Process:**

```python
def hash_password(password: str):
    """Hash using Argon2 - one-way encryption"""
    return password_context.hash(password)
```

## Testing Registration in Swagger

1. Go to Swagger: `http://127.0.0.1:8000/docs`
2. Click on `/register` endpoint
3. Click **"Try it out"** button
4. Swagger auto-fills with default values:
   ```json
   {
     "username": "testuser",
     "password": "testpassword",
     "email": "testuser@gmail.com"
   }
   ```
5. Click **"Execute"**

**Visual Output:**

![Register Success](images/register_success.png)

## Registration Response

**HTTP Status:** 200 OK

**Response Body:**

```json
{
  "msg": "User created successfully"
}
```

**What Happened in Database:**

New row added to `users` table:

```
| id | username  | password (hashed)              | email               |
|----|-----------|-------------------------------|---------------------|
| 1  | testuser  | $argon2id$v=19$m=65536$t=... | testuser@gmail.com |
```

**Important Security Points:**

- Actual password (`testpassword`) is **never stored**
- Only the Argon2 hash is saved
- If database is hacked, passwords can't be recovered
- Argon2 is modern & memory-hard (GPU resistant)

---

# PART 6: USER LOGIN

## Understanding the Login Code

```python
# In app.py
class UserLogin(BaseModel):
    username: str = "testuser"
    password: str = "testpassword"

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    # 1. Find user in database
    db_user = db.query(User).filter(
        User.username == user.username
    ).first()

    # 2. Verify password (compare plain text with stored hash)
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # 3. Create access token (expires in 2 minutes)
    access_token = create_access_token(data={"sub": db_user.username})

    # 4. Create refresh token (expires in 7 days)
    refresh_token = create_refresh_token(data={"sub": db_user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
```

**Code Explanation:**

1. **Query Database**: Find user by username
2. **Verify Password**: Compare plain text password with stored hash using Argon2
3. **Create Access Token**: Short-lived token (2 minutes) for API requests
4. **Create Refresh Token**: Long-lived token (7 days) to refresh access tokens

**Password Verification:**

```python
def verify_password(plain_password: str, hashed_password: str):
    """Compare plain password with stored hash"""
    return password_context.verify(plain_password, hashed_password)

# Compares: "testpassword" with "$argon2id$v=19$..."
# Returns: True (valid) or False (invalid)
```

## Testing Login in Swagger

1. Go to Swagger: `http://127.0.0.1:8000/docs`
2. Click on `/login` endpoint
3. Click **"Try it out"** button
4. Default values:
   ```json
   {
     "username": "testuser",
     "password": "testpassword"
   }
   ```
5. Click **"Execute"**

**Visual Output:**

![Login with Tokens](images/login_w_access_token.png)

## Login Response

**HTTP Status:** 200 OK

**Response Body:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcxMzM3MTkyMH0.UB7Bvj1Y...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcxNDk3Njc2MH0.kqL9Jz..."
}
```

**Token Details:**

| Token             | Duration  | Purpose                                        |
| ----------------- | --------- | ---------------------------------------------- |
| **access_token**  | 2 minutes | Use for API requests in `Authorization` header |
| **refresh_token** | 7 days    | Use to get new access_token when expired       |

**Token Structure (JWT):**

Each token is in format: `header.payload.signature`

```json
// Decoded access_token looks like:
{
  "sub": "testuser", // Subject = username
  "exp": 1713371920, // Expiration time (Unix timestamp)
  "iat": 1713371860 // Issued at time
}
```

**Save both tokens for next steps**

---

# PART 7: TRYING TO ACCESS WITHOUT TOKEN

## Accessing Protected Route (No Authorization)

First, let's try accessing a protected route **without any token**.

In Swagger:

1. Find `/users` endpoint
2. Click **"Try it out"**
3. Click **"Execute"**
4. **Do NOT authorize yet!**

**What Happens:**

The route is protected by:

```python
@app.get("/users", response_model=list[UserResponse])
def get_all_users(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # ← Requires token!
    db: Session = Depends(get_db)
):
    # Code never reaches here without valid token
    pass
```

## Error Response

**HTTP Status:** 401 Unauthorized

**Response Body:**

```json
{
  "detail": "Not authenticated"
}
```

**Visual Output:**

![Not Authorized](images/not_authorized.png)

**Why It Failed:**

The `HTTPBearer()` dependency looks for `Authorization: Bearer <token>` header:

- No header found = 401 "Not authenticated"
- Header missing = Request rejected immediately
- User code never executes

---

# PART 8: AUTHORIZE IN SWAGGER UI

## Click the Authorize Button

In Swagger UI, locate the green **"Authorize"** button (top-right corner)

**Visual Output:**

![Auth Token Fillup](images/auth_token_fillup.png)

## Enter Your Access Token

A dialog box appears:

```
Available authorizations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HTTPBearer (http, Bearer)
Value: ____________________________________
       [Authorize]  [Cancel]
```

**Steps:**

1. **Copy** your `access_token` from login response (Step 6)
2. **Paste** it in the Value field
   - Just the token itself (no "Bearer " prefix)
   - Swagger adds "Bearer " automatically
3. Click **"Authorize"** button

## Authorization Added

After clicking Authorize:

Swagger adds this header to **every** subsequent request:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Green lock icon appears on "Authorize" button

All endpoints now include your token automatically

**Behind the Scenes:**

```python
# When you authorize, Swagger does this for all requests:
# Add header: Authorization: Bearer <your_access_token>

# Your API receives request with header
# HTTPBearer extracts the token
# Token gets decoded and verified
# If valid, request proceeds
```

---

# PART 9: ACCESS PROTECTED ROUTE WITH VALID TOKEN

## Calling /users with Authorization

Now that you're authorized in Swagger, try again:

1. Find `/users` endpoint
2. Click **"Try it out"**
3. Click **"Execute"**

**What Happens:**

Your request now includes:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The API code executes:

```python
@app.get("/users", response_model=list[UserResponse])
def get_all_users(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    # 1. Extract token from Authorization header
    token = credentials.credentials
    # token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

    # 2. Decode and verify token
    payload = decode_access_token(token)
    # payload = {"sub": "testuser", "exp": 1713371920}

    # 3. Check if token is valid
    if payload is None:
        # Token expired or invalid
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # 4. Token is valid - fetch users
    users = db.query(User).all()
    return users
```

**Token Verification:**

```python
def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        return payload  #  Token valid
    except JWTError:
        return None  #  Token invalid or expired
```

## Success Response

**HTTP Status:** 200 OK

**Response Body:**

```json
[
  {
    "id": 1,
    "username": "testuser",
    "email": "testuser@gmail.com"
  }
]
```

**Visual Output:**

![Authorized Access](images/authorized.png)

**Important Notes:**

- Password is **NOT** included in response (security)
- Only public user info is returned (id, username, email)
- Token was verified and valid
- Request succeeded with 200 OK status

---

# PART 10: TOKEN EXPIRATION

## Wait for Token to Expire

Your access_token expires in **2 minutes**.

**Configuration (in `auth_utils.py`):**

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 2  # Your setting
```

The token contains expiration time:

```json
{
  "sub": "testuser",
  "exp": 1713371920,    ← Unix timestamp when token expires
  "iat": 1713371860     ← Unix timestamp when created
}
```

## Try Accessing After Expiration (2+ min later)

After 2 minutes and 1 second have passed:

1. Click `/users` endpoint
2. Click **"Try it out"**
3. Click **"Execute"**

## Expiration Error Response

**HTTP Status:** 401 Unauthorized

**Response Body:**

```json
{
  "detail": "Invalid or expired token"
}
```

**Visual Output:**

![Expired Token Error](images/expired_token.png)

**Why It Failed:**

When decoding the expired token:

```python
def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:  # ← Exception caught
        return None
```

**Error Flow:**

1. Token received: `eyJhbGciOi...`
2. Decoded successfully
3. Current time checked: `2024-04-30 10:02:00`
4. Expiration time: `2024-04-30 10:00:00`
5. Current > Expiration = EXPIRED
6. JWT raises JWTError
7. Function returns None
8. API returns 401 error

---

# PART 11: REFRESH TOKEN FOR NEW ACCESS TOKEN

## Understanding the Refresh Process

When your access_token expires, use refresh_token to get a new one **without logging in again**.

```python
@app.post("/refresh")
def refresh_token_endpoint(refresh_token: str):
    # 1. Decode refresh token
    payload = decode_refresh_token(refresh_token)

    # 2. Check if refresh token is valid
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    # 3. Create NEW access token with same username
    new_access_token = create_access_token(
        data={"sub": payload["sub"]}
    )

    return {"access_token": new_access_token}
```

## Testing Refresh in Swagger

1. Get your `refresh_token` from login response (Step 6)
2. In Swagger, click `/refresh` endpoint
3. Click **"Try it out"**
4. Paste your refresh_token in request body:
   ```json
   {
     "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcxNDk3Njc2MH0.kqL9Jz..."
   }
   ```
5. Click **"Execute"**

## Refresh Response

**HTTP Status:** 200 OK

**Response Body:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcxMzM3Mjc5MH0.xYz789..."
}
```

**New Access Token Details:**

- Brand new token
- Expires in 2 minutes (fresh countdown starts)
- Same username as before
- Different token string (different signature)
- Can be used immediately

## Use New Token for API Access

1. Click **"Authorize"** button again
2. Paste the new `access_token` in Value field
3. Click **"Authorize"**
4. Now you can call `/users` again for another 2 minutes!

**Complete Cycle:**

```
Login (get tokens)
    ↓
Use access_token for API calls (2 min window)
    ↓
Token expires → 401 "Invalid or expired token"
    ↓
Call /refresh with refresh_token
    ↓
Get new access_token
    ↓
Use new access_token for API calls (2 min window)
    ↓
Repeat process (refresh valid for 7 days)
    ↓
After 7 days: Must login again to get new refresh token
```
