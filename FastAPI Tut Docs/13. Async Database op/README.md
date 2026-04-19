# Tutorial: Asynchronous Database Operations

This tutorial highlights how to set up an **Asynchronous Database** architecture in FastAPI using `SQLAlchemy 2.0` and `asyncio`.

Using async databases allows FastAPI to maintain massive concurrency. Instead of locking up the server waiting for SQLite to write a row, it yields processing power to handle other user requests until the database finishes its job.

## The Code breakdown (`app.py`)

### 1. Imports

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
```

- `from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker`: These are the critical imports for async mode. Standard `create_engine` will block threads, but `create_async_engine` runs completely async.

### 2. Async Engine and Session Initialization

```python
engine=create_async_engine("sqlite+aiosqlite:///./test.db", connect_args={"check_same_thread": False})
SessionLocal=async_sessionmaker(autoflush=False, bind=engine)
```

- `sqlite+aiosqlite:///./test.db`: Notice the `+aiosqlite`. This specifies the asynchronous SQLite driver layer that tells SQLAlchemy how to communicate asynchronously with SQLite.
- `connect_args={"check_same_thread": False}`: SQLite exclusively locks threads. Since FastAPI hops connections across threads, this bypasses that restriction to prevent thread crashing.
- `async_sessionmaker(autoflush=False, bind=engine)`: Creates a database session factory, returning a unique, async connection (`AsyncSession`) every time we invoke `SessionLocal()`.

### 3. Creating the Database Base

```python
class Base(DeclarativeBase):
    pass
```

- `class Base(DeclarativeBase)`: Establishing the base foundation that our tables will inherit. This maps Python classes explicitly to SQL Tables. (Note: Previously done via `declarative_base()`, but `DeclarativeBase` is the modern SQLAlchemy 2.0 standard).

### 4. Defining the Database Model (Table)

```python
class User(Base):
    __tablename__="users"
    id=Column(Integer, primary_key=True, index=True)
    name=Column(String, index=True)
    email=Column(String, unique=True, index=True)
```

- `__tablename__="users"`: Tells the DB exactly what strings to name the SQL table.
- `Column(...)`: Maps standard SQL Columns directly into Python properties.
- `primary_key=True`: Establishes `id` as our unique identifier.
- `index=True`: Speeds up "where" queries searching along these table values.

### 5. Managing Lifespan & Sessions

```python
async def get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    db=SessionLocal()
    try:
        yield db
    finally:
        await db.close()
```

- `async with engine.begin() as conn:`: We open a specialized, high-level asynchronous context connection pool.
- `await conn.run_sync(Base.metadata.create_all)`: Interestingly, table **creation** does not have a pure async equivalent, so we use `run_sync` to wrap the standard sync table creation without blocking our thread. It creates `test.db` if it doesn't exist.
- `db=SessionLocal()`: Creates our actual `AsyncSession` object.
- `yield db`: Pauses execution, releasing the `db` variable into our API Routes.
- `finally: await db.close()`: The moment the route finishes providing a user response, FastAPI returns here and safely closes/tears down the database connection. `await` ensures the close completes asynchronously.

### 6. Defining Validation (Pydantic Schema)

```python
app=FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str
```

- `class UserCreate(BaseModel):`: Standard Pydantic model dictating what payload users must securely upload via JSON body when creating a specific user (stripping malicious inputs).

### 7. Creating Records (Async Insert)

```python
@app.post("/users/", response_model=UserCreate)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
```

- `async def create_user(...)`: Route explicitly marked `async` to handle awaitable operations.
- `db: AsyncSession = Depends(get_db)`: Depends dynamically injects our database session into our route, type hinting strictly as `AsyncSession`.
- `db.add(db_user)`: Stages the row. Doesn't write it to SQLite yet.
- `await db.commit()`: Using `await`, it sends the transaction asynchronously to SQLite. The FastAPI thread is completely free to handle other traffic until SQLite confirms successful write.
- `await db.refresh(db_user)`: Updates our local python `db_user` object with the newly created SQL `id` (asynchronously!).

### 8. Fetching Records (Async Select)

```python
@app.get("/users/")
async def read_users(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users
```

- `skip: int = 0, limit: int = 10`: Request Query parameters injected for automated pagination API support.
- `result = await db.execute(select(User).offset(skip).limit(limit))`: Execute queries completely asynchronously. Notice how we use traditional `select()` constructs passed into an asynchronous `.execute()` awaitable object.
- `users = result.scalars().all()`: Because the execute method initially returns a vast SQL Chunk object wrapper, `.scalars().all()` extracts purely the mapped ORM User objects straight into a Python list map.
