from fastapi import FastAPI
import json


app=FastAPI()

def json_load():
    with open("basic_view.json") as f:
        data = json.load(f)
    return data


@app.get("/")
def index():
    return {"message": "Welcome to the FastAPI application"}

@app.get("/view")
def view():
    data = json_load()
    return data

