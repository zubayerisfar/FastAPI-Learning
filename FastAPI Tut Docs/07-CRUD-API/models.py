from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from db import Base


class Item(Base):
    __tablename__ = "items"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    