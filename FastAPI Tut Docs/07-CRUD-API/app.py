from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from db import SessionLocal, engine, Base
from models import Item
import uvicorn  

# Create tables on startup
Base.metadata.create_all(bind=engine)


# Pydantic Schemas
class ItemCreate(BaseModel):
    name: str
    price: float
    quantity: float


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    quantity: float


# Dependency to get database session
def get_db():
    """Dependency: Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


# CREATE - Add new item
@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Create a new item"""
    db_item = Item(name=item.name, price=item.price, quantity=item.quantity)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


# READ - Get all items
@app.get("/items/", response_model=List[ItemResponse])
def read_items(db: Session = Depends(get_db)):
    """Get all items"""
    query = select(Item)
    items = db.execute(query).scalars().all()
    return items


# READ - Get single item
@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific item by ID"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


# UPDATE - Modify item
@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    """Update an existing item"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.name = item.name
    db_item.price = item.price
    db_item.quantity = item.quantity
    db.commit()
    db.refresh(db_item)
    return db_item


# DELETE - Remove item
@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Delete an item"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)