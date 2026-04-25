import os
from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine

# Define models that work as both ORM and Pydantic schemas


class Item(SQLModel, table=True):
    """Item model - combines ORM and Pydantic validation"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    is_offer: bool = False


class ItemCreate(SQLModel):
    """Schema for creating items (no id field)"""
    name: str
    price: float
    is_offer: bool = False


# Configure MySQL connection
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "fastapi_db")

mysql_url = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

engine = create_engine(mysql_url, echo=True)


def create_db_and_tables() -> None:
    """Create database tables on startup"""
    SQLModel.metadata.create_all(engine)
