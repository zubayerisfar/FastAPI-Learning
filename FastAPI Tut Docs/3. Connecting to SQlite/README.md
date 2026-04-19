# Tutorial: Connecting FastAPI to SQLite Database

## Overview

This tutorial teaches you how to connect a FastAPI application to a SQLite database using **SQLModel**, which is a modern library that combines the power of SQLAlchemy and Pydantic. We'll build a simple Item API that can create and retrieve items from a SQLite database.

## Project Structure

```
3. Connecting to SQLite/
├── database_setup.py  # Database configuration and table models
└── main.py           # FastAPI application with endpoints
```

---

## Step 1: Database Setup (`database_setup.py`)

First, we need to set up our database connection and define our data models. Open `database_setup.py` and add this code:

```python
from sqlmodel import Field, SQLModel, create_engine
from typing import Optional
```

**Line-by-line explanation:**

- `from sqlmodel import Field, SQLModel, create_engine`: Import essential SQLModel components
  - `Field`: Used to define column properties (primary keys, defaults, etc.)
  - `SQLModel`: The base class for creating database models
  - `create_engine`: Creates the database connection engine
- `from typing import Optional`: Import Optional for nullable fields

### Define the Data Model

```python
class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    is_offer: bool = False
```

**Line-by-line explanation:**

- `class Item(SQLModel, table=True):`: Create a model class that inherits from SQLModel
  - `table=True`: This tells SQLModel to create an actual database table for this class
  - Without `table=True`, it would just be a Pydantic model without database mapping
- `id: Optional[int] = Field(default=None, primary_key=True)`:
  - `Optional[int]`: The id can be None before insertion (database will auto-generate it)
  - `Field(...)`: Defines special properties for this column
  - `default=None`: When creating a new item, id starts as None
  - `primary_key=True`: Makes this the primary key (unique identifier for each row)
- `name: str`: A required string field (cannot be None)
- `price: float`: A required float field for the item price
- `is_offer: bool = False`: A boolean field with a default value of False

### Configure the Database Connection

```python
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
```

**Line-by-line explanation:**

- `sqlite_file_name = "database.db"`: The name of the SQLite database file
  - This file will be created in the same directory as your script
  - SQLite is a file-based database, so all data is stored in this single file
- `sqlite_url = f"sqlite:///{sqlite_file_name}"`: Create the database URL
  - Format: `sqlite:///filename.db`
  - The three slashes `///` indicate a relative path
  - This URL tells SQLAlchemy how to connect to the database

### Create the Database Engine

```python
engine = create_engine(sqlite_url, echo=True)
```

**Line-by-line explanation:**

- `create_engine(...)`: Creates the engine that manages database connections
  - `sqlite_url`: The connection string we created above
  - `echo=True`: Enables SQL query logging - you'll see all SQL statements in the console
  - This is very helpful for learning and debugging
  - Set to `False` in production to reduce console noise

### Create Table Function

```python
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

**Line-by-line explanation:**

- `def create_db_and_tables():`: Function that creates all database tables
- `SQLModel.metadata.create_all(engine)`:
  - `metadata`: Contains information about all tables defined with SQLModel
  - `create_all(engine)`: Creates all tables that don't exist yet
  - This is idempotent - running it multiple times won't cause errors
  - If tables already exist, it does nothing

---

## Step 2: FastAPI Application (`main.py`)

Now let's create our FastAPI application that uses this database. Open `main.py`:

```python
from typing import List
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database_setup import Item, create_db_and_tables, engine
from sqlmodel import Session, select
```

**Line-by-line explanation:**

- `from typing import List`: For type hints with lists
- `from fastapi import FastAPI`: Import the FastAPI class
- `from contextlib import asynccontextmanager`: For creating async context managers
  - This is crucial for managing startup/shutdown events
- `from database_setup import Item, create_db_and_tables, engine`:
  - Import our model, table creation function, and database engine
- `from sqlmodel import Session, select`:
  - `Session`: Used to interact with the database (add, query, commit)
  - `select`: Used to build SQL SELECT queries

### Lifespan Context Manager

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
```

**Line-by-line explanation:**

- `@asynccontextmanager`: Decorator that makes this an async context manager
  - Context managers handle setup (before yield) and cleanup (after yield)
- `async def lifespan(app: FastAPI):`: Define the lifespan function
  - This function controls what happens during app startup and shutdown
  - `app: FastAPI`: Receives the FastAPI application instance
- `create_db_and_tables()`: **RUNS ON STARTUP**
  - This executes when the server starts
  - Creates all database tables before any requests are handled
- `yield`: **THE DIVIDING LINE**
  - Everything before `yield` runs on startup
  - Everything after `yield` runs on shutdown
  - The `yield` statement keeps the application running between startup and shutdown
  - In this example, we have no shutdown code, but you could add database cleanup after yield

**Why is lifespan so important?**

- Without it, tables might not exist when the first request comes in
- It ensures database initialization happens exactly once at startup
- It provides a clean way to manage resources (connections, background tasks, etc.)
- FastAPI guarantees this runs before accepting any HTTP requests

### Create the FastAPI App

```python
app = FastAPI(lifespan=lifespan)
```

**Line-by-line explanation:**

- `app = FastAPI(lifespan=lifespan)`: Create the FastAPI application instance
  - `lifespan=lifespan`: Attach our lifespan context manager
  - FastAPI will automatically call our lifespan function to manage startup/shutdown

### Create Item Endpoint

```python
@app.post("/items/")
def create_item(item: Item):
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
```

**Line-by-line explanation:**

- `@app.post("/items/")`: Define a POST endpoint at `/items/`
  - POST is the HTTP method used for creating resources
- `def create_item(item: Item):`: The endpoint function
  - `item: Item`: FastAPI automatically validates incoming JSON against the Item model
  - Thanks to Pydantic/SQLModel, invalid data is rejected automatically
- `with Session(engine) as session:`: Create a database session
  - `with`: Context manager that automatically closes the session when done
  - `Session(engine)`: Creates a new session using our database engine
  - Sessions manage transactions and track changes
- `session.add(item)`: Add the item to the session
  - This stages the item for insertion
  - Nothing is written to the database yet
- `session.commit()`: Commit the transaction
  - This executes the INSERT SQL statement
  - Writes the item to the database
  - The database generates the `id` value
- `session.refresh(item)`: Refresh the item from the database
  - This loads the auto-generated `id` back into our item object
  - Without this, `item.id` would still be None
- `return item`: Return the complete item (including its new id) as JSON

### Read Items Endpoint

```python
@app.get("/items/", response_model=List[Item])
def read_items():
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        return items
```

**Line-by-line explanation:**

- `@app.get("/items/", response_model=List[Item])`: Define a GET endpoint
  - `response_model=List[Item]`: Tells FastAPI the response is a list of Items
  - This enables automatic validation and documentation
- `def read_items():`: The endpoint function (no parameters needed)
- `with Session(engine) as session:`: Create a database session
- `items = session.exec(select(Item)).all()`:
  - `select(Item)`: Create a SQL SELECT query for all Item records
  - This is equivalent to SQL: `SELECT * FROM item`
  - `session.exec(...)`: Execute the query
  - `.all()`: Fetch all results as a list
- `return items`: Return the list of items as JSON

---

## How to Run This Project

1. **Install dependencies:**

   ```bash
   pip install fastapi uvicorn sqlmodel
   ```

2. **Start the server:**

   ```bash
   uvicorn main:app --reload
   ```

   - `main:app`: Points to the `app` object in `main.py`
   - `--reload`: Auto-restarts the server when code changes

3. **Test the API:**
   - Visit `http://127.0.0.1:8000/docs` for interactive API documentation
   - Create an item: POST to `/items/` with JSON body:
     ```json
     {
       "name": "Laptop",
       "price": 999.99,
       "is_offer": false
     }
     ```
   - Get all items: GET request to `/items/`

---

## Key Concepts Summary

1. **SQLModel**: Combines Pydantic (validation) + SQLAlchemy (database ORM)
2. **Engine**: The database connection manager
3. **Session**: A workspace for database operations (think of it as a transaction)
4. **Lifespan**: Manages startup/shutdown logic - CRITICAL for initialization
5. **Context Managers (`with`)**: Automatically handle resource cleanup
6. **Type Hints**: Enable automatic validation and great IDE support

## What Happens Behind the Scenes?

1. **Server starts** → `lifespan` function executes → Tables are created
2. **POST request arrives** → FastAPI validates JSON → Creates Item instance → Opens session → Adds to DB → Commits → Returns response
3. **GET request arrives** → Opens session → Queries all items → Returns JSON list
4. **Server stops** → `lifespan` cleanup code runs (after yield)

This pattern forms the foundation for all database operations in FastAPI!
