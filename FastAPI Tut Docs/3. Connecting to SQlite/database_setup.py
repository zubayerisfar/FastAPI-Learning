from sqlmodel import Field, SQLModel, create_engine
from typing import Optional

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    is_offer: bool = False
    
sqlite_file_name = "database.db"
sqlite_url =f"sqlite:///{sqlite_file_name}"

engine= create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)