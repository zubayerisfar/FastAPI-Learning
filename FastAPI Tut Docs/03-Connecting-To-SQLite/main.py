from typing import List
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database_setup import Item, create_db_and_tables, engine
from sqlmodel import Session, select, SQLModel
import uvicorn


# Request model without ID (for POST requests)
class ItemCreate(SQLModel):
    name: str
    price: float
    is_offer: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate):
    with Session(engine) as session:
        # Convert ItemCreate to Item (with default id=None for auto-increment)
        db_item = Item.from_orm(item)
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
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
    