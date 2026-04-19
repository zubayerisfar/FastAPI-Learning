from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

# Ollama server runs locally
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Request model
class Message(BaseModel):
    message: str

@app.post("/chat")
def chat(message: Message):
    # Send request to Ollama
    payload = {
        "model": "gemma3:1b",     # you can change to any model you have (mistral, codellama, etc.)
        "prompt": message.message,
        "stream": False
    }
    
    response = requests.post(OLLAMA_API_URL, json=payload)

    if response.status_code != 200:
        return {"error": "Failed to get response", "details": response.text}

    result = response.json()
    return {"answer": result["response"]}
