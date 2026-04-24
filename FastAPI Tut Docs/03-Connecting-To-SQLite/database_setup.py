from sqlmodel import Field, SQLModel, create_engine
from typing import Optional
import os

class Item(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None, 
        primary_key=True,
        sa_column_kwargs={"autoincrement": True}  # This enables auto-increment
    )
    name: str
    price: float
    is_offer: bool = False


# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))
sqlite_file_name = os.path.join(current_dir, "database.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
