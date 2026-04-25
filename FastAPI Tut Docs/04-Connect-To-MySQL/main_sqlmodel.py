from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI
from sqlmodel import Session, select
from database_setup_sqlmodel import Item, ItemCreate, create_db_and_tables, engine
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler - creates tables on startup"""
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate):
    """Create a new item"""
    with Session(engine) as session:
        db_item = Item.model_validate(item)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item


@app.get("/items/", response_model=List[Item])
def read_items():
    """Read all items"""
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        return items


@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int):
    """Read a specific item by ID"""
    with Session(engine) as session:
        item = session.exec(select(Item).where(Item.id == item_id)).first()
        if item is None:
            return {"error": "Item not found"}
        return item


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: ItemCreate):
    """Update an existing item"""
    with Session(engine) as session:
        db_item = session.exec(select(Item).where(Item.id == item_id)).first()
        if db_item is None:
            return {"error": "Item not found"}
        db_item.name = item.name
        db_item.price = item.price
        db_item.is_offer = item.is_offer
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    """Delete an item"""
    with Session(engine) as session:
        db_item = session.exec(select(Item).where(Item.id == item_id)).first()
        if db_item is None:
            return {"error": "Item not found"}
        session.delete(db_item)
        session.commit()
        return {"message": "Item deleted successfully"}


if __name__ == "__main__":
    uvicorn.run("main_sqlmodel:app", host="127.0.0.1", port=8000, reload=True)
