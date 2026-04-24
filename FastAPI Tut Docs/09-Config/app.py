from fastapi import FastAPI
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

import os

load_dotenv()


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL")
    secret_key: str = os.getenv("SECRET_KEY")


settings = Settings()
app = FastAPI()

print(settings.database_url)


@app.get("/")
async def read_root():
    return {"message": "Configuration Loaded Successfully!",
            "database_url": settings.database_url,
            "secret_key": settings.secret_key
            }
