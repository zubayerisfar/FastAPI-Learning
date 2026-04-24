from pydantic import BaseModel
from fastapi import FastAPI

app = FastAPI()


class ResponseModel(BaseModel):
    name: str
    price: float
    is_offer: bool = False


class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False
    password: str = "Dont show this"


@app.post("/items/")
def create_item(item: Item):
    return {
        "message": "item created successfully",
        "item": item
    }


@app.post("/items2/", response_model=ResponseModel)
def create_item(item: Item):
    return item
