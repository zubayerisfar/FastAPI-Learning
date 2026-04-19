from fastapi import FastAPI, HTTPException
from langchain_ollama import OllamaLLM

model=OllamaLLM(model="gemma3:1b",temperature=.6)

app=FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chat")
def chat(message):
    response=model.invoke(message)
    return response