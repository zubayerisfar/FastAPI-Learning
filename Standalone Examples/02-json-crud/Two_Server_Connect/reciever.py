# app.py
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI()
API_KEY = "supersecret"  # store as env var in real use

class Query(BaseModel):
    user_id: int
    question: str

class Answer(BaseModel):
    status: str
    reply: str

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="gemma3:1b", temperature=0.6)

@app.post("/ask", response_model=Answer)
def ask(q: Query, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(401, "Unauthorized")
    # do your logic here
    response = llm.invoke(q.question)
    return {"status": "ok", "reply": response}
