from fastapi import FastAPI
from pydantic import BaseModel
from db import SessionLocal, base, engine
from models import Item

class ItemSchema(BaseModel):
    name: str
    price:int
    quantity: float

app= FastAPI()

base.metadata.create_all(bind=engine)


@app.post("/items/")
def create_item(item: ItemSchema):
    db_item = Item(name=item.name, price=item.price, quantity=item.quantity)
    with SessionLocal() as session:
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
    return db_item

@app.get("/items/{item_id}")
def read_item(item_id: int):
    with SessionLocal() as session:
        db_item = session.query(Item).filter(Item.id == item_id).first()
        if db_item is None:
            return {"error": "Item not found"}
    return db_item


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

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    with SessionLocal() as session:
        db_item = session.query(Item).filter(Item.id == item_id).first()
        if db_item is None:
            return {"error": "Item not found"}
        session.delete(db_item)
        session.commit()
    return {"message": "Item deleted successfully"}