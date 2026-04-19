# Tutorial: Building a Complete CRUD API with FastAPI

## Overview

This tutorial teaches you how to build a full **CRUD (Create, Read, Update, Delete)** API using FastAPI with SQLAlchemy ORM. This is different from previous tutorials - instead of SQLModel, we use the traditional SQLAlchemy approach with separate Pydantic schemas. This pattern is widely used in production applications and gives you fine-grained control over your database models and API schemas.

## What is CRUD?

**CRUD** stands for the four basic operations on data:

- **C**reate: Add new records (POST)
- **R**ead: Retrieve records (GET)
- **U**pdate: Modify existing records (PUT)
- **D**elete: Remove records (DELETE)

Every database-backed application needs these operations!

## Project Structure

```
7. CRUD API/
├── db.py         # Database configuration with SQLAlchemy
├── models.py     # Database ORM models
└── app.py        # FastAPI application with CRUD endpoints
```

---

## Step 1: Database Configuration (`db.py`)

We'll set up SQLAlchemy with the **declarative base** pattern.

```python
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
```

**Line-by-line explanation:**

- `from sqlalchemy import create_engine, MetaData`:
  - `create_engine`: Creates the database connection engine
  - `MetaData`: Container for database schema information (not used here but imported for completeness)
- `from sqlalchemy.orm import declarative_base, sessionmaker`:
  - `declarative_base`: **SQLAlchemy 2.0 syntax** - creates the base class for ORM models
  - In older versions, this was `from sqlalchemy.ext.declarative import declarative_base`
  - `sessionmaker`: Factory for creating database sessions

### Define Database URL

```python
DATABASE_URL = "sqlite:///./database.db"
```

**Line-by-line explanation:**

- `DATABASE_URL`: Connection string for SQLite
- `sqlite:///./database.db`: Creates `database.db` file in current directory
  - `sqlite:///`: SQLite protocol
  - `./database.db`: Relative path to database file
  - For production, use PostgreSQL: `postgresql://user:pass@host:port/dbname`

### Create Database Engine

```python
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

**Line-by-line explanation:**

- `create_engine(DATABASE_URL, ...)`: Create the database engine
  - The engine manages the connection pool
  - Handles low-level database communication
- `connect_args={"check_same_thread": False}`:
  - **SQLite-specific configuration**
  - By default, SQLite only allows connections from the thread that created them
  - `check_same_thread": False` disables this check
  - **Why?** FastAPI uses multiple threads/workers
  - **Not needed for PostgreSQL/MySQL** - only SQLite has this limitation

### Create Base Class

```python
base = declarative_base()
```

**Line-by-line explanation:**

- `base = declarative_base()`: Creates the base class for ORM models
  - All your models will inherit from this base
  - This base class provides:
    - Database table mapping
    - Column definitions
    - Relationships
    - Query capabilities
  - **This is the foundation of SQLAlchemy ORM**

**What does it do?**

- When you create a class inheriting from `base`, SQLAlchemy knows it's a database table
- The base tracks all models for table creation
- Enables `base.metadata.create_all(engine)` to create all tables

### Create Session Factory

```python
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
)
```

**Line-by-line explanation:**

- `SessionLocal = sessionmaker(...)`: Create a session factory

  - **Not a session itself** - it's a factory that creates sessions
  - Think of it as a "session constructor"
  - Naming convention: `SessionLocal` indicates it's for local use

- `bind=engine`: Bind this session factory to our engine

  - All sessions created will use this engine
  - Connects sessions to our database

- `autoflush=False`: Disable automatic flushing
  - **Flush**: Sync Python objects to database without committing
  - `False`: You manually control when to flush
  - Gives you more control over when SQL is executed
  - **Default is True** - changes automatically sync to DB

**Missing parameter:** `autocommit=False` is the default

- `False`: Transactions must be manually committed
- This is what you want - explicit transaction control

---

## Step 2: Database Models (`models.py`)

Now we define the database table structure using SQLAlchemy ORM.

```python
from sqlalchemy import Column, Integer, String, Float
from db import base
```

**Line-by-line explanation:**

- `from sqlalchemy import Column, Integer, String, Float`: Column types
  - `Column`: Defines a table column
  - `Integer`: Integer data type
  - `String`: Variable-length string (VARCHAR in SQL)
  - `Float`: Floating-point number
- `from db import base`: Import the declarative base from db.py
  - Our Item model will inherit from this base

### Define the Item Model

```python
class Item(base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    quantity = Column(Integer, default=0)
```

**Line-by-line explanation:**

- `class Item(base):`: Define a model class inheriting from base
  - **Inheritance from base** tells SQLAlchemy this is a database table
  - Class name `Item` is the Python name (singular)
- `__tablename__ = "items"`: The actual table name in the database

  - **Required**: Tells SQLAlchemy what to name the SQL table
  - By convention, use lowercase plural: "items", "users", "products"
  - SQL table will be named `items`

- `id = Column(Integer, primary_key=True, index=True)`: Primary key column

  - `Column(...)`: Define a table column
  - `Integer`: Data type - whole numbers
  - `primary_key=True`: This is the primary key
    - Auto-incrementing (SQLite: AUTOINCREMENT, PostgreSQL: SERIAL)
    - Unique identifier for each row
    - Cannot be NULL
  - `index=True`: Create a database index on this column
    - Makes lookups by ID very fast
    - Automatically indexed for primary keys, but explicit is clear

- `name = Column(String, index=True)`: Name column

  - `String`: Variable-length text (no length limit specified)
  - For production, specify length: `String(100)`
  - `index=True`: Create index for fast searches by name
    - **Use indexes for columns you frequently search/filter by**
    - Makes `WHERE name = ?` queries much faster

- `price = Column(Float)`: Price column

  - `Float`: Decimal numbers (e.g., 19.99, 1234.56)
  - **Note**: For money, use `DECIMAL` in production: `Column(DECIMAL(10, 2))`
  - Float has precision issues with money calculations

- `quantity = Column(Integer, default=0)`: Quantity column
  - `Integer`: Whole numbers
  - `default=0`: If not provided, defaults to 0
    - This is a **database-level default**
    - New rows without quantity will automatically get 0

**What SQLAlchemy generates:**

```sql
CREATE TABLE items (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR,
    price FLOAT,
    quantity INTEGER DEFAULT 0
);
CREATE INDEX ix_items_id ON items (id);
CREATE INDEX ix_items_name ON items (name);
```

---

## Step 3: FastAPI Application (`app.py`)

Now let's build the complete CRUD API.

```python
from fastapi import FastAPI
from pydantic import BaseModel
from db import SessionLocal, base, engine
from models import Item
```

**Line-by-line explanation:**

- `from fastapi import FastAPI`: The FastAPI class
- `from pydantic import BaseModel`: For request/response validation schemas
- `from db import SessionLocal, base, engine`:
  - `SessionLocal`: Session factory for database operations
  - `base`: Declarative base for creating tables
  - `engine`: Database engine
- `from models import Item`: Our ORM model

### Define Pydantic Schema

```python
class ItemSchema(BaseModel):
    name: str
    price: int
    quantity: float
```

**Line-by-line explanation:**

- `class ItemSchema(BaseModel):`: Pydantic model for validation

  - **Separate from ORM model!**
  - `Item` (models.py) = Database table
  - `ItemSchema` (app.py) = API request/response format

- `name: str`: Name must be a string
- `price: int`: Price as integer (note: model has Float)
- `quantity: float`: Quantity as float

**Why separate schemas?**

1. **Security**: Don't expose all database fields to API
2. **Flexibility**: API format can differ from database format
3. **Validation**: Different validation rules for input vs database

### Create FastAPI App

```python
app = FastAPI()
```

**Line-by-line explanation:**

- `app = FastAPI()`: Create the FastAPI application instance

### Create Database Tables

```python
base.metadata.create_all(bind=engine)
```

**Line-by-line explanation:**

- `base.metadata.create_all(bind=engine)`: Create all tables
  - `base.metadata`: Contains info about all models inheriting from base
  - `.create_all(...)`: Generate and execute CREATE TABLE statements
  - `bind=engine`: Use this engine for the connection
  - **Idempotent**: Safe to run multiple times (won't recreate existing tables)
  - **Runs at module load time** (when Python imports app.py)

---

## CREATE: Add New Item

```python
@app.post("/items/")
def create_item(item: ItemSchema):
    db_item = Item(name=item.name, price=item.price, quantity=item.quantity)
    with SessionLocal() as session:
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
    return db_item
```

**Line-by-line explanation:**

- `@app.post("/items/")`: POST endpoint at `/items/`

  - POST is the HTTP method for creating resources
  - Trailing slash is a convention

- `def create_item(item: ItemSchema):`: Endpoint function
  - `item: ItemSchema`: FastAPI validates JSON against ItemSchema
  - Automatic validation and error messages

**Step 1: Create ORM instance**

```python
db_item = Item(name=item.name, price=item.price, quantity=item.quantity)
```

- `Item(...)`: Create an instance of the ORM model
  - Not yet in the database - just a Python object
  - Maps Pydantic schema to ORM model
  - `id` is not set - database will auto-generate it

**Step 2: Open database session**

```python
with SessionLocal() as session:
```

- `SessionLocal()`: Create a new database session
  - Calls the factory we created in db.py
  - Returns a Session object for database operations
- `with ... as session:`: Context manager
  - **Automatically closes the session** when done
  - Handles errors gracefully
  - Prevents session leaks

**Step 3: Add item to session**

```python
session.add(db_item)
```

- `session.add(db_item)`: Stage the item for insertion
  - Adds item to the session's pending changes
  - **No SQL executed yet**
  - Item is tracked by the session

**Step 4: Commit the transaction**

```python
session.commit()
```

- `session.commit()`: Save changes to database
  - Executes `INSERT INTO items ...` SQL
  - Makes changes permanent
  - Database generates the `id` (auto-increment)
  - If error occurs, changes are rolled back

**Step 5: Refresh the object**

```python
session.refresh(db_item)
```

- `session.refresh(db_item)`: Reload object from database
  - Fetches the database-generated `id`
  - Without this, `db_item.id` would be None
  - Ensures the object matches what's in the database

**Step 6: Return the item**

```python
return db_item
```

- Returns the ORM object as JSON
- FastAPI automatically serializes it
- Response includes the generated `id`

**Example request:**

```json
POST /items/
{
  "name": "Laptop",
  "price": 999,
  "quantity": 5.0
}
```

**Example response:**

```json
{
  "id": 1,
  "name": "Laptop",
  "price": 999.0,
  "quantity": 5
}
```

---

## READ: Get Single Item

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    with SessionLocal() as session:
        db_item = session.query(Item).filter(Item.id == item_id).first()
        if db_item is None:
            return {"error": "Item not found"}
    return db_item
```

**Line-by-line explanation:**

- `@app.get("/items/{item_id}")`: GET endpoint with path parameter

  - `{item_id}`: Path parameter - captures value from URL
  - Example URL: `/items/5` → `item_id = 5`

- `def read_item(item_id: int):`: Endpoint function
  - `item_id: int`: FastAPI converts URL parameter to integer
  - Validates it's a number - rejects `/items/abc`

**Open session**

```python
with SessionLocal() as session:
```

- Same pattern as create - context manager

**Query the database**

```python
db_item = session.query(Item).filter(Item.id == item_id).first()
```

- `session.query(Item)`: Start a query on Item table
  - Returns a Query object
  - Equivalent to `SELECT * FROM items`
- `.filter(Item.id == item_id)`: Add WHERE clause
  - `Item.id`: The id column
  - `== item_id`: Equality comparison
  - Equivalent to `WHERE id = ?`
  - **Security**: SQLAlchemy prevents SQL injection
- `.first()`: Execute and get first result
  - Returns one Item object or None
  - Use `.all()` for all results
  - Use `.one()` to require exactly one result (errors otherwise)

**Equivalent SQL:**

```sql
SELECT * FROM items WHERE id = ? LIMIT 1
```

**Check if found**

```python
if db_item is None:
    return {"error": "Item not found"}
```

- If no item with that ID exists, return error
- **Better practice**: Raise HTTPException(404)

**Return the item**

```python
return db_item
```

- Returns the ORM object as JSON

**Example:** GET `/items/1`

```json
{
  "id": 1,
  "name": "Laptop",
  "price": 999.0,
  "quantity": 5
}
```

---

## UPDATE: Modify Existing Item

```python
@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemSchema):
    with SessionLocal() as session:
        db_item = session.query(Item).filter(Item.id == item_id).first()
        if db_item is None:
            return {"error": "Item not found"}
        db_item.name = item.name
        db_item.price = item.price
        db_item.quantity = item.quantity
        session.commit()
        session.refresh(db_item)
    return db_item
```

**Line-by-line explanation:**

- `@app.put("/items/{item_id}")`: PUT endpoint

  - PUT is the HTTP method for updating resources
  - Requires the full object (replace entire item)
  - For partial updates, use PATCH

- `def update_item(item_id: int, item: ItemSchema):`: Two parameters
  - `item_id: int`: Which item to update (from URL)
  - `item: ItemSchema`: New data (from request body)

**Find the item**

```python
db_item = session.query(Item).filter(Item.id == item_id).first()
if db_item is None:
    return {"error": "Item not found"}
```

- Query for the item by ID
- Return error if not found

**Update the fields**

```python
db_item.name = item.name
db_item.price = item.price
db_item.quantity = item.quantity
```

- Update the ORM object's attributes
- **Just modifying Python object** - not yet in database
- SQLAlchemy tracks these changes

**Commit the changes**

```python
session.commit()
```

- Executes `UPDATE items SET name=?, price=?, quantity=? WHERE id=?`
- Makes changes permanent in database

**Refresh the object**

```python
session.refresh(db_item)
```

- Reload from database
- Ensures object matches database state

**Return updated item**

```python
return db_item
```

**Example request:**

```json
PUT /items/1
{
  "name": "Gaming Laptop",
  "price": 1299,
  "quantity": 3.0
}
```

**Example response:**

```json
{
  "id": 1,
  "name": "Gaming Laptop",
  "price": 1299.0,
  "quantity": 3
}
```

---

## DELETE: Remove Item

```python
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    with SessionLocal() as session:
        db_item = session.query(Item).filter(Item.id == item_id).first()
        if db_item is None:
            return {"error": "Item not found"}
        session.delete(db_item)
        session.commit()
    return {"message": "Item deleted successfully"}
```

**Line-by-line explanation:**

- `@app.delete("/items/{item_id}")`: DELETE endpoint

  - DELETE is the HTTP method for removing resources

- `def delete_item(item_id: int):`: Takes only ID parameter
  - No request body needed - just delete by ID

**Find the item**

```python
db_item = session.query(Item).filter(Item.id == item_id).first()
if db_item is None:
    return {"error": "Item not found"}
```

- Must find the item first to delete it
- Return error if doesn't exist

**Delete the item**

```python
session.delete(db_item)
```

- `session.delete(db_item)`: Mark item for deletion
  - Stages the delete operation
  - **No SQL executed yet**

**Commit the deletion**

```python
session.commit()
```

- Executes `DELETE FROM items WHERE id = ?`
- Permanently removes the row

**Return success message**

```python
return {"message": "Item deleted successfully"}
```

- Confirm deletion to client
- Common to return 204 No Content instead

**Example:** DELETE `/items/1`

```json
{
  "message": "Item deleted successfully"
}
```

---

## Complete CRUD Operation Flow

### 1. CREATE (POST /items/)

```
Client sends JSON → Validate with ItemSchema → Create ORM object →
session.add() → session.commit() → session.refresh() → Return with ID
```

### 2. READ (GET /items/1)

```
Client requests → session.query() → filter by ID → .first() →
Return item or error
```

### 3. UPDATE (PUT /items/1)

```
Client sends JSON → Find item → Update attributes → session.commit() →
session.refresh() → Return updated item
```

### 4. DELETE (DELETE /items/1)

```
Client requests → Find item → session.delete() → session.commit() →
Return success message
```

---

## How to Run This Project

### 1. Install Dependencies

```bash
pip install fastapi uvicorn sqlalchemy
```

### 2. Start the Server

```bash
uvicorn app:app --reload
```

### 3. Test the API

Visit `http://127.0.0.1:8000/docs` for interactive API documentation.

#### Create an item:

```bash
curl -X POST http://127.0.0.1:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Mouse","price":25,"quantity":10}'
```

#### Get item:

```bash
curl http://127.0.0.1:8000/items/1
```

#### Update item:

```bash
curl -X PUT http://127.0.0.1:8000/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Wireless Mouse","price":35,"quantity":8}'
```

#### Delete item:

```bash
curl -X DELETE http://127.0.0.1:8000/items/1
```

---

## Best Practices and Improvements

### 1. Use HTTPException for Errors

```python
from fastapi import HTTPException

if db_item is None:
    raise HTTPException(status_code=404, detail="Item not found")
```

### 2. Use Dependency Injection for Sessions

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/{item_id}")
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item
```

### 3. Separate Response Models

```python
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    quantity: int

    class Config:
        from_attributes = True

@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int):
    # ...
```

### 4. Add Pagination for List Endpoints

```python
@app.get("/items/")
def list_items(skip: int = 0, limit: int = 10):
    with SessionLocal() as session:
        items = session.query(Item).offset(skip).limit(limit).all()
        return items
```

### 5. Use Transactions Properly

```python
def update_item(item_id: int, item: ItemSchema):
    with SessionLocal() as session:
        try:
            db_item = session.query(Item).filter(Item.id == item_id).first()
            if not db_item:
                raise HTTPException(404, "Not found")
            db_item.name = item.name
            session.commit()
            session.refresh(db_item)
            return db_item
        except Exception as e:
            session.rollback()
            raise
```

---

## Common Issues and Solutions

### Issue 1: "Table already exists" Error

**Solution:** `create_all()` is idempotent - this shouldn't happen unless migrations are needed.

### Issue 2: Session Not Closed

**Solution:** Always use context managers (`with SessionLocal() as session:`)

### Issue 3: DetachedInstanceError

**Solution:** Access all needed attributes before session closes, or use `session.refresh()`

### Issue 4: Data Type Mismatch

**Solution:** Ensure Pydantic schema matches ORM model types

---

## Key Concepts Summary

1. **SQLAlchemy ORM**: Maps Python classes to database tables
2. **Declarative Base**: Foundation for ORM models
3. **Session**: Workspace for database operations (like a transaction)
4. **Context Manager**: `with SessionLocal()` ensures cleanup
5. **CRUD Operations**: Create (POST), Read (GET), Update (PUT), Delete (DELETE)
6. **session.add()**: Stage new objects
7. **session.commit()**: Save changes permanently
8. **session.refresh()**: Reload object from database
9. **session.query()**: Start a SELECT query
10. **Separation of Concerns**: ORM models vs Pydantic schemas

## Architecture Pattern

```
Client Request
     ↓
FastAPI Endpoint
     ↓
Pydantic Validation (ItemSchema)
     ↓
SessionLocal (Database Session)
     ↓
SQLAlchemy ORM (Item model)
     ↓
SQLite Database
```

This is a production-ready pattern used by thousands of applications!
