# Connecting FastAPI to MySQL Database

## Overview

This tutorial shows how to connect a FastAPI application to a real MySQL database. The code is almost identical to using SQLite, but now your data lives on a MySQL server instead of a single file. This is what production applications use.

The two files you need to understand are:

- **database_setup.py**: Configures MySQL connection and defines the Item table
- **main.py**: Creates the API endpoints that use that database

## Project Structure

```
4. Connect to MySQL/
├── database_setup.py  # Database configuration with MySQL
└── main.py           # FastAPI application (identical to SQLite version)
```

---

## Before You Start

You'll need:

- **MySQL Server** running (XAMPP, MySQL Community Server, or Docker)
- **Python packages**: `pip install fastapi uvicorn sqlmodel pymysql cryptography`

---

## Understanding the Database Model

Let's look at how we define the Item table in `database_setup.py`:

```python
class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None,
                            primary_key=True,
                            sa_column_kwargs={"autoincrement": True})
    name: str
    price: float
    is_offer: bool = False
```

**What each line does:**

- `class Item(SQLModel, table=True):` - Creates a table in MySQL called "item"
- `id: Optional[int]` - The primary key, can be None when creating (MySQL generates it)
- `Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})` - Makes MySQL auto-increment the id automatically
- `name: str`, `price: float`, `is_offer: bool = False` - The actual data fields

The key insight: You define Python classes, SQLModel converts them to database tables. No need to write SQL CREATE statements yourself.

---

## Connecting to MySQL Server

When you start the FastAPI app, it automatically creates the table in MySQL. Here's what happens behind the scenes:

```python
mysql_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
```

This connection string tells Python: "Connect to MySQL using pymysql driver, with these credentials, at this host and port, and use this database."

The format is: `mysql+pymysql://username:password@localhost:3306/database_name`

By default (from environment variables):

- Username: `root`
- Password: (empty)
- Host: `localhost`
- Port: `3306`
- Database: `fastapi_db`

```python
engine = create_engine(mysql_url, echo=True)
```

The engine manages the connection. `echo=True` prints all SQL queries to console so you can see what's happening.

```python
def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
```

This function runs automatically when your app starts. It creates the Item table in MySQL if it doesn't exist.

### What Table Creation Looks Like

When you run the app, FastAPI creates the table and logs SQL. Here's what you see in XAMPP:

![Database table created at startup](images/database_created.png)

---

## The Complete database_setup.py

Here's the full database configuration file for reference:

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