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
