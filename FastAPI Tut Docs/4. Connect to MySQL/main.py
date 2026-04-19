from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI
from sqlmodel import Session, select
from database_setup import Item, create_db_and_tables,engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/items/", response_model=Item)
def create_item(item: Item):
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item


@app.get("/items/", response_model=List[Item])
def read_items():
    with Session(engine) as session:
        items=session.exec(select(Item)).all()
        return items
