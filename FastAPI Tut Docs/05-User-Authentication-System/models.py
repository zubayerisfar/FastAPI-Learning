from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True)
    age: Mapped[int] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
