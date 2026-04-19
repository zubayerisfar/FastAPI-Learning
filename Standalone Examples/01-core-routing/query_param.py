from fastapi import FastAPI,Query,HTTPException
import json


app = FastAPI()


def load_json():
    with open("basic_view.json") as f:
        return json.load(f)
    
@app.get("/")
def index():
    return {"message": "Welcome to the API"}

@app.get('/sort')
def sort_items(sort_by:str=Query(...,description="The column across the data will be sorted"),sort_order:str=Query("asc",description="The order in which the data will be sorted")):
    sort_options=["name","city","age"]
    if sort_by not in sort_options:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by value. Choose from {sort_options}")
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail='Invalid sort_order value. Choose either "asc" or "desc".')
    
    sort_order=False if sort_order=="asc" else True

    data=load_json()
    sorted_data=sorted(data.values(),key=lambda x: x.get(sort_by,0),reverse=sort_order)
    return sorted_data