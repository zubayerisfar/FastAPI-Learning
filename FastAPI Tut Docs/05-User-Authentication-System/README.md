# Tutorial: Building a User Authentication System with FastAPI

## Overview

This tutorial teaches you how to build a complete user authentication system with **secure password hashing** using FastAPI. You'll learn about async database operations, password security with bcrypt, and how to structure a multi-file authentication system. This is a foundational pattern for any application that needs user accounts.

## Project Structure

```
5. User Authentication System/
├── db.py          # Async database configuration
├── models.py      # Database table definition
├── schema.py      # Pydantic models for request validation
└── app.py         # FastAPI application with register/login endpoints
```

---

## Why This Architecture?

**Separation of Concerns:**

- `db.py`: Database connection only
- `models.py`: Database table structure
- `schema.py`: Input/output data validation
- `app.py`: Business logic and endpoints

This makes the code maintainable, testable, and follows industry best practices.

---

## Step 1: Database Configuration (`db.py`)

First, we set up an **async** database connection. This is different from previous tutorials because authentication operations should be non-blocking.

```python
from sqlalchemy import create_engine, MetaData
from databases import Database
```

**Line-by-line explanation:**

- `from sqlalchemy import create_engine, MetaData`: SQLAlchemy for database schema
  - `create_engine`: Creates the sync engine for table creation
  - `MetaData`: Container for table definitions
- `from databases import Database`: **The `databases` library for async queries**
  - This is different from SQLModel! It provides async/await support
  - Install with: `pip install databases[sqlite]`

### Define the Database URL

```python
DATABASE_URL = f"sqlite:///./users.db"
```

**Line-by-line explanation:**

- `DATABASE_URL`: Connection string for SQLite database
- `f"sqlite:///./users.db"`: Creates a file named `users.db` in current directory
  - The `f` prefix is technically unnecessary here (no variables), but keeps it consistent
  - For production, use PostgreSQL: `postgresql://user:pass@host:port/db`

### Create Database Objects

```python
database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL)
```

**Line-by-line explanation:**

- `database = Database(DATABASE_URL)`: **The async database client**

  - This object provides async methods: `fetch_one()`, `execute()`, `fetch_all()`
  - Used for all runtime queries (register, login, etc.)
  - Must be connected before use (done in app.py lifespan)

- `metadata = MetaData()`: **Container for table schemas**

  - Stores information about all tables you define
  - Tables are registered with this metadata object
  - Used to create all tables at once

- `engine = create_engine(DATABASE_URL)`: **Synchronous engine for setup**
  - Used only for creating tables (one-time operation)
  - Not used for queries - that's what `database` is for
  - No connection pooling needed since it's only for startup

**Why two database objects?**

- `database`: Async operations (fast, non-blocking queries)
- `engine`: Sync operations (table creation at startup)

---

## Step 2: Database Models (`models.py`)

Now we define the database table structure using SQLAlchemy Core (not ORM).

```python
from sqlalchemy import create_engine, Table, Column, Integer, String
from db import metadata
```

**Line-by-line explanation:**

- `from sqlalchemy import create_engine, Table, Column, Integer, String`: SQLAlchemy components
  - `Table`: Defines a database table
  - `Column`: Defines a table column
  - `Integer, String`: Column data types
- `from db import metadata`: Import the metadata container from db.py
  - Our table will be registered with this metadata

### Define the Users Table

```python
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(50), unique=True, nullable=False, index=True),
    Column("age", Integer, nullable=False),
    Column("password", String(), nullable=False)
)
```

**Line-by-line explanation:**

- `users = Table(`: Create a Table object
  - This represents the `users` table in the database
- `"users",`: **First parameter: table name in the database**
  - The actual SQL table will be named "users"
- `metadata,`: **Second parameter: the metadata container**

  - Registers this table with our metadata object
  - Enables `metadata.create_all(engine)` to create this table

- `Column("id", Integer, primary_key=True),`: **ID column**

  - `"id"`: Column name
  - `Integer`: Data type
  - `primary_key=True`: Auto-incrementing unique identifier
  - SQLite automatically makes this an AUTOINCREMENT field

- `Column("username", String(50), unique=True, nullable=False, index=True),`: **Username column**

  - `String(50)`: Maximum 50 characters
  - `unique=True`: No two users can have the same username
  - `nullable=False`: This field is required (cannot be NULL)
  - `index=True`: Creates a database index for fast lookups
    - **Why?** Usernames are frequently searched during login
    - Indexes make queries much faster

- `Column("age", Integer, nullable=False),`: **Age column**

  - Required integer field
  - No special constraints

- `Column("password", String(), nullable=False)`: **Password column**
  - `String()`: Unlimited length (needed for hashed passwords)
  - Hashed passwords are ~60 characters (bcrypt output)
  - `nullable=False`: Password is required

**Important Security Note:**
The password will store the **hashed** version, never the plain text!

---

## Step 3: Request/Response Schemas (`schema.py`)

Define the data structures for API requests using Pydantic.

```python
from pydantic import BaseModel
```

**Line-by-line explanation:**

- `from pydantic import BaseModel`: Base class for data validation models
  - Pydantic automatically validates incoming JSON
  - Provides great error messages for invalid data

### Registration Schema

```python
class Register(BaseModel):
    username: str
    age: int
    password: str
```

**Line-by-line explanation:**

- `class Register(BaseModel):`: Model for registration requests
- `username: str`: Required string field
  - Pydantic ensures this is present and is a string
- `age: int`: Required integer field
  - Pydantic converts numeric strings to int
  - Rejects non-numeric values
- `password: str`: Required string field
  - This receives the plain text password
  - We'll hash it before storing (never store plain text!)

**Example valid request:**

```json
{
  "username": "john_doe",
  "age": 25,
  "password": "secure_password_123"
}
```

### Login Schema

```python
class Login(BaseModel):
    username: str
    password: str
```

**Line-by-line explanation:**

- `class Login(BaseModel):`: Model for login requests
- Only needs username and password
- Age is not required for login (it's already in the database)

**Example valid request:**

```json
{
  "username": "john_doe",
  "password": "secure_password_123"
}
```

---

## Step 4: FastAPI Application (`app.py`)

Now we bring it all together with the authentication logic.

```python
from fastapi import FastAPI, HTTPException
from passlib.context import CryptContext
from contextlib import asynccontextmanager
from db import database, engine, metadata
from models import users
from schema import Register, Login
```

**Line-by-line explanation:**

- `from fastapi import FastAPI, HTTPException`:
  - `FastAPI`: The application class
  - `HTTPException`: Used to return error responses (400, 404, etc.)
- `from passlib.context import CryptContext`: **Password hashing library**

  - Passlib is the industry standard for password hashing
  - Supports multiple algorithms (bcrypt, argon2, pbkdf2, etc.)
  - Install: `pip install "passlib[bcrypt]" bcrypt==3.2.2`

- `from contextlib import asynccontextmanager`: For lifespan management

- `from db import database, engine, metadata`: Database objects

  - `database`: Async client for queries
  - `engine`: Sync engine for table creation
  - `metadata`: Table schemas

- `from models import users`: The users table definition

- `from schema import Register, Login`: Request validation models

### Create Database Tables

```python
metadata.create_all(engine)
```

**Line-by-line explanation:**

- `metadata.create_all(engine)`: Create all tables at module load time
  - This runs **immediately** when Python imports this file
  - Creates the `users` table if it doesn't exist
  - **Why here and not in lifespan?**
    - For async databases, we need the sync engine for table creation
    - Lifespan is async, so we do sync operations outside it

### Configure Password Hashing

```python
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

**Line-by-line explanation:**

- `password_context = CryptContext(...)`: Create a password hashing context
- `schemes=["bcrypt"]`: Use the bcrypt algorithm

  - **Bcrypt** is specifically designed for passwords
  - Slow by design - makes brute force attacks impractical
  - Automatically handles salting (random data added to passwords)
  - Output format: `$2b$12$salt.hash` (60 characters)

- `deprecated="auto"`: Handle deprecated hash formats automatically
  - If you upgrade algorithms later, old hashes still work
  - Automatically rehash passwords on next login

**Two critical methods:**

1. `password_context.hash(plain_password)`: Hash a password → Returns bcrypt string
2. `password_context.verify(plain_password, hashed)`: Check if password matches → Returns True/False

### Lifespan Context Manager

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: code before yield runs on startup
    await database.connect()
    yield
    # Shutdown: code after yield runs on shutdown
    await database.disconnect()
```

**Line-by-line explanation:**

- `@asynccontextmanager`: Decorator for async context managers
- `async def lifespan(app: FastAPI):`: Async lifespan function

- `await database.connect()`: **STARTUP - Connect to database**

  - Opens the connection pool
  - Must be called before any queries
  - This is **async** - doesn't block the event loop
  - Runs once when the server starts

- `yield`: **THE DIVIDING LINE**

  - App runs here (between startup and shutdown)
  - All requests are handled during this period

- `await database.disconnect()`: **SHUTDOWN - Close database connections**
  - Gracefully closes all connections
  - Runs when the server is shutting down (Ctrl+C, etc.)
  - Ensures no database connection leaks

**Why async connect/disconnect?**

- Non-blocking - server stays responsive
- Proper resource management
- Enables connection pooling

### Create the FastAPI App

```python
app = FastAPI(lifespan=lifespan)
```

**Line-by-line explanation:**

- `app = FastAPI(lifespan=lifespan)`: Create app with lifespan management
  - FastAPI automatically manages startup and shutdown

---

## Register Endpoint

```python
@app.post("/register")
async def register(user: Register):
    query = users.select().where(users.c.username == user.username)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username Already Exists")
    hashed_password = password_context.hash(user.password)
    query = users.insert().values(username=user.username,
                                age=user.age, password=hashed_password)
    await database.execute(query)
    return {"message": "User registered successfully!"}
```

**Line-by-line explanation:**

- `@app.post("/register")`: POST endpoint at `/register`

  - POST because we're creating a new resource (user)

- `async def register(user: Register):`: Async endpoint function
  - `async`: Enables non-blocking I/O
  - `user: Register`: FastAPI validates against Register schema

**Step 1: Check if username exists**

```python
query = users.select().where(users.c.username == user.username)
```

- `users.select()`: Build a SELECT query
- `.where(users.c.username == user.username)`: Filter by username
  - `users.c.username`: The username column (`.c` = "columns")
  - Equivalent SQL: `SELECT * FROM users WHERE username = ?`

```python
existing_user = await database.fetch_one(query)
```

- `await database.fetch_one(query)`: Execute query and get one result
  - Returns a Row object if found, None if not found
  - `await`: Non-blocking database call

```python
if existing_user:
    raise HTTPException(status_code=400, detail="Username Already Exists")
```

- If user exists, return 400 Bad Request error
- `HTTPException`: FastAPI converts this to a JSON error response
- Prevents duplicate usernames

**Step 2: Hash the password**

```python
hashed_password = password_context.hash(user.password)
```

- `password_context.hash(user.password)`: Hash the plain text password
  - Input: `"mypassword123"`
  - Output: `"$2b$12$abc...xyz"` (60 characters)
  - **CRITICAL**: Never store the original password!
  - Each hash is unique due to automatic salting

**Step 3: Insert the new user**

```python
query = users.insert().values(username=user.username,
                            age=user.age, password=hashed_password)
```

- `users.insert()`: Build an INSERT query
- `.values(...)`: Set the column values
  - Uses the **hashed** password, not the original
  - Equivalent SQL: `INSERT INTO users (username, age, password) VALUES (?, ?, ?)`

```python
await database.execute(query)
```

- Execute the INSERT query
- `await`: Non-blocking
- The database auto-generates the `id` field

**Step 4: Return success response**

```python
return {"message": "User registered successfully!"}
```

- Returns JSON: `{"message": "User registered successfully!"}`
- Status code is 200 by default

---

## Login Endpoint

```python
@app.post("/login")
async def login(user: Login):
    query = users.select().where(users.c.username == user.username)
    existing_user = await database.fetch_one(query)
    if not existing_user:
        raise HTTPException(status_code=400, detail="Invalid Username or Password")

    is_valid = password_context.verify(user.password, existing_user.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid Username or Password")

    return {"message": "Login successful!"}
```

**Line-by-line explanation:**

- `@app.post("/login")`: POST endpoint at `/login`

- `async def login(user: Login):`: Async function with Login validation

**Step 1: Find the user**

```python
query = users.select().where(users.c.username == user.username)
existing_user = await database.fetch_one(query)
```

- Query the database for the username
- Same pattern as registration

**Step 2: Check if user exists**

```python
if not existing_user:
    raise HTTPException(status_code=400, detail="Invalid Username or Password")
```

- If user doesn't exist, return error
- **Security Note**: We say "Invalid Username or Password" instead of "User not found"
  - This prevents username enumeration attacks
  - Attackers can't tell if a username exists

**Step 3: Verify the password**

```python
is_valid = password_context.verify(user.password, existing_user.password)
```

- `password_context.verify(plain_password, hashed_password)`: Check password
  - **First parameter**: Plain text password from request
  - **Second parameter**: Hashed password from database
  - Returns `True` if match, `False` if not

**How it works:**

1. Extracts the salt from the stored hash
2. Hashes the input password with that salt
3. Compares the hashes
4. Time-constant comparison (prevents timing attacks)

**Step 4: Check verification result**

```python
if not is_valid:
    raise HTTPException(status_code=400, detail="Invalid Username or Password")
```

- If password doesn't match, return error
- Same error message as "user not found" (security best practice)

**Step 5: Return success**

```python
return {"message": "Login successful!"}
```

- Login succeeded!
- In a real app, you'd return a JWT token here

---

## How to Run This Project

### 1. Install Dependencies

```bash
pip install fastapi uvicorn databases[sqlite] "passlib[bcrypt]" bcrypt==3.2.2
```

**Why `bcrypt==3.2.2`?**

- Newer bcrypt versions have compatibility issues with passlib
- Version 3.2.2 is stable and works perfectly

### 2. Start the Server

```bash
uvicorn app:app --reload
```

### 3. Test Registration

Visit `http://127.0.0.1:8000/docs` and test POST to `/register`:

```json
{
  "username": "alice",
  "age": 28,
  "password": "secret123"
}
```

Response:

```json
{
  "message": "User registered successfully!"
}
```

### 4. Test Login

POST to `/login`:

```json
{
  "username": "alice",
  "password": "secret123"
}
```

Response:

```json
{
  "message": "Login successful!"
}
```

### 5. Test Wrong Password

POST to `/login`:

```json
{
  "username": "alice",
  "password": "wrong_password"
}
```

Response (400 error):

```json
{
  "detail": "Invalid Username or Password"
}
```

---

## Security Concepts Explained

### 1. Password Hashing

**Never store plain text passwords!**

- Plain text: `"mypassword123"`
- Hashed: `"$2b$12$LQzf6vKkY3xS..."`
- Even if database is leaked, passwords are safe

### 2. Salting

- **Salt**: Random data added to password before hashing
- Each password gets a unique salt
- Prevents rainbow table attacks
- Bcrypt handles this automatically

### 3. Timing-Safe Comparison

- `verify()` takes constant time regardless of correctness
- Prevents attackers from deducing passwords through timing

### 4. Error Message Uniformity

- "Invalid Username or Password" for both cases
- Doesn't reveal if username exists
- Prevents username enumeration

### 5. Async Database Operations

- Non-blocking I/O
- Server handles thousands of requests efficiently
- Critical for scalability

---

## Common Errors and Solutions

### Error: "module 'bcrypt' has no attribute '**about**'"

**Solution:** Install bcrypt 3.2.2

```bash
pip install bcrypt==3.2.2
```

### Error: "password cannot be longer than 72 bytes"

**Solution:** This is a bcrypt limitation. For very long passwords, hash them with SHA256 first:

```python
import hashlib
prehashed = hashlib.sha256(long_password.encode()).hexdigest()
final_hash = password_context.hash(prehashed)
```

### Error: "Database is locked"

**Solution:** SQLite doesn't handle high concurrency well. Use PostgreSQL for production:

```python
DATABASE_URL = "postgresql://user:pass@localhost/dbname"
```

---

## Next Steps: Production Improvements

1. **Add JWT tokens** for session management
2. **Use PostgreSQL** instead of SQLite
3. **Add email verification** for new accounts
4. **Implement rate limiting** to prevent brute force
5. **Add password strength requirements**
6. **Implement refresh tokens** for security
7. **Add two-factor authentication (2FA)**

---

## Key Concepts Summary

1. **Async Database**: `databases` library for non-blocking queries
2. **Password Hashing**: Passlib with bcrypt - never store plain text
3. **Salting**: Automatic with bcrypt - unique salt per password
4. **Lifespan Management**: Connect on startup, disconnect on shutdown
5. **Schema Separation**: Pydantic for validation, SQLAlchemy for database
6. **Security**: Timing-safe verification, uniform error messages
7. **HTTPException**: Clean error responses with status codes

## Authentication Flow Diagram

**Registration:**

1. User sends username/password
2. Check if username exists → 400 if yes
3. Hash password with bcrypt
4. Insert user with hashed password
5. Return success message

**Login:**

1. User sends username/password
2. Query database for username → 400 if not found
3. Verify password against hash → 400 if wrong
4. Return success (in real apps: return JWT token)

This is the foundation of modern authentication systems!
