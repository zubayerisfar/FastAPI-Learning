# Connecting FastAPI to MySQL Database

## Overview

This tutorial shows how to connect a FastAPI application to a real MySQL database using **SQLAlchemy ORM** with dependency injection. The same pattern works for SQLite, PostgreSQL, and other databases. This is the industry-standard approach used in production applications.

The two files you need to understand are:

- **database_setup.py**: Configures MySQL connection and defines the Item ORM model
- **main.py**: Creates the API endpoints that use that database

## Project Structure

```
04-Connect-To-MySQL/
├── database_setup.py  # Database configuration with MySQL, ORM models, and Pydantic schemas
└── main.py           # FastAPI application with dependency injection
```

---

## Before You Start

You'll need:

- **MySQL Server** running (XAMPP, MySQL Community Server, or Docker)
- **Python packages**: `pip install fastapi uvicorn sqlalchemy pymysql cryptography pydantic`

---

## Step 1: Database Configuration (`database_setup.py`)

### Import SQLAlchemy Components

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel
```

**Explanation:**

- `Column`: Define database table columns
- `create_engine`: Manages database connections
- `declarative_base`: Base class for ORM models
- `sessionmaker`: Factory for database sessions
- `BaseModel`: Pydantic for API request/response validation

### Define the ORM Model

```python
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    price = Column(Float)
    is_offer = Column(Boolean, default=False)
```

**What each line does:**

- `class Item(Base):` - Creates a class that will map to a MySQL table
- `__tablename__ = "items"` - The actual table name in MySQL
- `id = Column(Integer, primary_key=True, ...)` - Primary key with auto-increment
- `name = Column(String, index=True)` - Text field with database index for faster queries
- `price = Column(Float)` - Decimal numbers
- `is_offer = Column(Boolean, default=False)` - Boolean with default value

**Key Difference from SQLModel:**

- SQLModel combines ORM and Pydantic into one class
- SQLAlchemy ORM keeps them separate (better for complex apps)

### Define Pydantic Schemas

```python
class ItemCreate(BaseModel):
    name: str
    price: float
    is_offer: bool = False


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    is_offer: bool
```

**Why two schemas?**

- `ItemCreate`: For incoming API requests (no id, user doesn't provide it)
- `ItemResponse`: For outgoing API responses (includes id that database generated)

This separation is cleaner and more secure than mixing database and API concerns.

### Connect to MySQL

```python
mysql_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
engine = create_engine(mysql_url, echo=True)
SessionLocal = sessionmaker(autoflush=False, bind=engine)
```

**Explanation:**

- `mysql_url`: Connection string format: `mysql+pymysql://user:pass@host:port/database`
- `engine`: Manages the connection pool
- `echo=True`: Prints all SQL to console (remove for production)
- `SessionLocal`: Factory for creating database sessions

By default (from environment variables):

- Username: `root`
- Password: (empty)
- Host: `localhost`
- Port: `3306`
- Database: `fastapi_db`

### Create Tables at Startup

```python
def create_db_and_tables() -> None:
    Base.metadata.create_all(engine)
```

This function creates the MySQL table if it doesn't exist. We call it in `main.py`.

---

## Step 2: FastAPI Application (`main.py`)

### Initialize the App

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

# Create tables on startup
create_db_and_tables()

app = FastAPI()
```

### Database Session Dependency

```python
def get_db():
    """Dependency: Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Why dependency injection?**

- Automatic session management (no forgetting to close)
- Easier to test (mock the dependency)
- FastAPI handles it automatically
- Used in every endpoint

### CREATE - Add New Item

```python
@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, price=item.price, is_offer=item.is_offer)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

**Flow:**

1. User sends POST request with JSON: `{"name": "Book", "price": 15.99, "is_offer": true}`
2. FastAPI validates with `ItemCreate` Pydantic schema
3. `get_db()` automatically provides a database session
4. Create ORM object from Pydantic data
5. `db.add()` prepares it for insertion
6. `db.commit()` writes to MySQL
7. `db.refresh()` gets the generated id
8. Return with `ItemResponse` schema (includes id)

### READ - Get All Items

```python
@app.get("/items/", response_model=List[ItemResponse])
def read_items(db: Session = Depends(get_db)):
    query = select(Item)
    items = db.execute(query).scalars().all()
    return items
```

**Modern SQLAlchemy 2.0 syntax:**

- `select(Item)`: Build query (like SQL: `SELECT * FROM items`)
- `db.execute(query)` Executes the query
- `.scalars()`: Extract the Item objects (not tuples)
- `.all()`: Get all results (or use `.first()` for one)

### READ - Get Single Item

```python
@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item
```

**Error Handling:**

- Check if item exists
- Raise 404 if not found
- Return item if found

### UPDATE - Modify Item

```python
@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.name = item.name
    db_item.price = item.price
    db_item.is_offer = item.is_offer
    db.commit()
    db.refresh(db_item)
    return db_item
```

**Steps:**

1. Find the item by id
2. Update all fields
3. Commit changes to MySQL
4. Return updated item

### DELETE - Remove Item

```python
@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}
```

---

## Running the Application

```bash
python main.py
```

The app will:

1. Create MySQL tables (if they don't exist)
2. Start the FastAPI server on http://127.0.0.1:8000
3. Print all SQL queries to console

---

## Testing with curl

### Create Item

```bash
curl -X POST http://localhost:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Book","price":15.99,"is_offer":true}'
```

### Get All Items

```bash
curl http://localhost:8000/items/
```

### Get Single Item

```bash
curl http://localhost:8000/items/1
```

### Update Item

```bash
curl -X PUT http://localhost:8000/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Book","price":12.99,"is_offer":false}'
```

### Delete Item

```bash
curl -X DELETE http://localhost:8000/items/1
```

---

## Key Differences: SQLModel vs SQLAlchemy ORM

| Aspect          | SQLModel             | SQLAlchemy ORM    |
| --------------- | -------------------- | ----------------- |
| **Combines**    | ORM + Pydantic       | Separate models   |
| **Boilerplate** | Less                 | More              |
| **Flexibility** | Limited              | High              |
| **Production**  | Good for simple apps | Industry standard |
| **Learning**    | Easier               | More to learn     |

---

## What's Happening in MySQL

When you run the app, it creates this table:

```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    price FLOAT NOT NULL,
    is_offer BOOLEAN DEFAULT FALSE
);
```

You can see this in XAMPP's phpmyadmin:

![Database table created](images/database_created.png)

---

## 🔄 Alternative Approach: Using SQLModel (Simpler Pattern)

This module uses **SQLAlchemy ORM** with separate Pydantic schemas (recommended for production). However, there's an alternative approach using **SQLModel** that combines both concerns in a single model class.

### SQLModel Approach: `database_setup_sqlmodel.py` & `main_sqlmodel.py`

**Files available in this folder:**

- `database_setup_sqlmodel.py` - SQLModel version
- `main_sqlmodel.py` - SQLModel version (run with: `python main_sqlmodel.py`)

#### Model Definition (SQLModel Way)

```python
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session

# Single class serves as BOTH ORM and Pydantic schema
class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    is_offer: bool = False

class ItemCreate(SQLModel):
    name: str
    price: float
    is_offer: bool = False
```

**vs SQLAlchemy ORM way:**

```python
from sqlalchemy import Column, Integer, String, Float, Boolean
from pydantic import BaseModel

# Separate ORM model
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
    is_offer = Column(Boolean)

# Separate Pydantic schema
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    is_offer: bool
```

#### Creating Items (SQLModel Way)

```python
@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate):
    with Session(engine) as session:
        db_item = Item.model_validate(item)  # Convert to full Item
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item
```

**vs SQLAlchemy ORM way:**

```python
@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, price=item.price, is_offer=item.is_offer)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

#### Reading Items (SQLModel Way)

```python
@app.get("/items/", response_model=List[Item])
def read_items():
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        return items
```

**vs SQLAlchemy ORM way:**

```python
@app.get("/items/", response_model=List[ItemResponse])
def read_items(db: Session = Depends(get_db)):
    query = select(Item)
    items = db.execute(query).scalars().all()
    return items
```

#### Session Management (SQLModel Way)

```python
# Uses context managers - simpler but less flexible
with Session(engine) as session:
    items = session.exec(select(Item)).all()
```

**vs SQLAlchemy ORM way:**

```python
# Uses dependency injection - more powerful and testable
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
def read_items(db: Session = Depends(get_db)):
    items = db.execute(select(Item)).scalars().all()
```

#### Startup Pattern (SQLModel Way)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield  # App runs here
    # Cleanup here if needed
```

**vs SQLAlchemy ORM way:**

```python
# Direct call at module level
create_db_and_tables()

app = FastAPI()  # No lifespan needed
```

### Comparison: SQLModel vs SQLAlchemy ORM

| Feature                | SQLModel             | SQLAlchemy ORM (This Module) |
| ---------------------- | -------------------- | ---------------------------- |
| **Lines of Code**      | Fewer                | More                         |
| **Learning Curve**     | Easier               | Steeper                      |
| **Type Hints**         | Good                 | Excellent                    |
| **Production Ready**   | Yes, for simple apps | Yes, industry standard       |
| **Flexibility**        | Limited              | High                         |
| **Schema Separation**  | Combined             | Separated                    |
| **Session Management** | Context managers     | Dependency injection         |
| **Scalability**        | Good                 | Excellent                    |
| **Job Market**         | Growing              | Most jobs                    |
| **Best For**           | Learning, prototypes | Production apps              |

### When to Use Each

**Use SQLModel (`main_sqlmodel.py`) when:**

- Building small projects
- Learning FastAPI basics
- Rapid prototyping
- API response exactly matches database
- You want less boilerplate

**Use SQLAlchemy ORM (`main.py`) when:**

- Building production applications
- Database schema differs from API response
- Need custom validation per endpoint
- Complex queries and relationships
- Testing is important
- Team needs maintainability

### Running Both Versions

**SQLAlchemy ORM version (recommended):**

```bash
python main.py
```

**SQLModel version:**

```bash
python main_sqlmodel.py
```

Both start on `http://127.0.0.1:8000` - don't run them simultaneously on the same port!

```python
import os
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None,
                            primary_key=True,
                            sa_column_kwargs={"autoincrement": True})
    name: str
    price: float
    is_offer: bool = False


class ItemCreate(SQLModel):
    name: str
    price: float
    is_offer: bool = False


# Configure MySQL connection (change defaults or use environment variables)
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "fastapi_db")

mysql_url = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

engine = create_engine(mysql_url, echo=True)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
```

**Note about ItemCreate:** We separate request validation from database storage. Users send JSON without an id, ItemCreate validates it, then we convert it to the full Item model which includes the database-generated id.

---

## Building the API Endpoints

The FastAPI endpoints are simple. Here's the complete application:

```python
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI
from sqlmodel import Session, select
from database_setup import Item, ItemCreate, create_db_and_tables, engine
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate):
    with Session(engine) as session:
        db_item = Item.model_validate(item)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item


@app.get("/items/", response_model=List[Item])
def read_items():
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        return items


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
```

### Understanding Each Endpoint

**The POST endpoint (Creating items):**

```python
@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate):
    with Session(engine) as session:
        db_item = Item.model_validate(item)  # Convert request to full Item model
        session.add(db_item)                  # Stage for insertion
        session.commit()                      # Execute INSERT in MySQL
        session.refresh(db_item)              # Load the auto-generated id
        return db_item
```

`Item.model_validate(item)` converts the ItemCreate request (without id) into an Item (with id field ready for MySQL). When you commit, MySQL generates the id automatically, then refresh loads it back.

**The GET endpoint (Reading items):**

```python
@app.get("/items/", response_model=List[Item])
def read_items():
    with Session(engine) as session:
        items = session.exec(select(Item)).all()  # Query all rows from MySQL
        return items
```

This opens a session, queries all items from the Item table, and returns them as JSON.

**The lifespan context manager:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  # Runs when app starts
    yield                   # App runs here
    # Cleanup would go after yield
```

This ensures the table exists before any request arrives. Without it, the first request would fail if the table hasn't been created yet.

---

## Getting Ready to Run

### Step 1: Create the MySQL Database

Before running the app, MySQL needs the `fastapi_db` database to exist:

```bash
mysql -u root -p
```

Then in the MySQL prompt:

```sql
CREATE DATABASE fastapi_db;
```

### Step 2: Install Packages

```bash
pip install fastapi uvicorn sqlmodel pymysql cryptography
```

### Step 3: Start the App

```bash
python main.py
```

Or if running from a different directory:

```bash
cd "04-Connect-To-MySQL"
python main.py
```

You should see output like `Uvicorn running on http://127.0.0.1:8000`. Open that URL in your browser to access the interactive API documentation.

---

## Testing the API

Open `http://127.0.0.1:8000/docs` in your browser. You'll see Swagger UI with two endpoints ready to test.

### Testing POST (Creating Items)

Click the POST endpoint `/items/` and click "Try it out". You'll see the request body template:

```json
{
  "name": "string",
  "price": 0,
  "is_offer": true
}
```

Try creating an item. Replace with real data:

```json
{
  "name": "Wireless Mouse",
  "price": 25.99,
  "is_offer": false
}
```

Click "Execute" and you get back the same data plus the `id` that MySQL generated.

### What's Happening in the Database

When you click POST multiple times without changing the data, each request creates a new row with an auto-incrementing id. Here's what it looks like in XAMPP Admin:

![Data added to MySQL after clicking POST button multiple times](images/database_added.png)

Notice how the `id` increases automatically. You never send an id in the request, but MySQL generates it. The `price` field stores the decimal values exactly as sent. The `is_offer` field is true (1) or false (0) in MySQL.

### Testing GET (Reading All Items)

Click the GET endpoint `/items/` and click "Try it out". Click "Execute" without changing anything. You get back all items created so far as a JSON array:

```json
[
  {
    "id": 1,
    "name": "Wireless Mouse",
    "price": 25.99,
    "is_offer": false
  },
  {
    "id": 2,
    "name": "Keyboard",
    "price": 49.99,
    "is_offer": true
  }
]
```

Here's the browser view showing the GET response:

![GET endpoint returns all items from database](images/get_items.png)

Each request to GET queries the MySQL server and returns the current state of the Item table.

---
