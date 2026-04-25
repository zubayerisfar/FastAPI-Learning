from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from database_setup import Item, ItemCreate, ItemResponse, SessionLocal, create_db_and_tables, engine
import uvicorn


# Create tables on startup
create_db_and_tables()


def get_db():
    """Dependency: Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, price=item.price, is_offer=item.is_offer)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/items/", response_model=List[ItemResponse])
def read_items(db: Session = Depends(get_db)):
    query = select(Item)
    items = db.execute(query).scalars().all()
    return items


@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """Read a specific item by ID"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    """Update an existing item"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.name = item.name
    db_item.price = item.price
    db_item.is_offer = item.is_offer
    db.commit()
    db.refresh(db_item)
    return db_item


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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
