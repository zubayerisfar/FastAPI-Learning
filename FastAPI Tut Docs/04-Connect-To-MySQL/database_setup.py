import os
from sqlalchemy import Column, Integer, String, Float, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel


class Base(declarative_base()):
    pass


# ORM Model - defines the database table
class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    price = Column(Float)
    is_offer = Column(Boolean, default=False)


# Pydantic Schema - for API request/response
class ItemCreate(BaseModel):
    name: str
    price: float
    is_offer: bool = False


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    is_offer: bool


# Configure MySQL connection (change defaults or use environment variables)
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "fastapi_db")

mysql_url = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

engine = create_engine(mysql_url, echo=True)

SessionLocal = sessionmaker(autoflush=False, bind=engine)


def create_db_and_tables() -> None:
    Base.metadata.create_all(engine)
