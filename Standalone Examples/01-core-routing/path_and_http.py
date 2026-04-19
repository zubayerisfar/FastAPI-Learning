from fastapi import FastAPI,Path,HTTPException
import json


app = FastAPI()


def load_json():
    with open("basic_view.json") as f:
        return json.load(f)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def get_item(item_id:str=Path(..., description="The ID of the item to retrieve")):
    data = load_json()
    if(item_id in data.keys()):
        return data[item_id]
    raise HTTPException(status_code=404, detail="Item not found")