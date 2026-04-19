from pydantic import BaseModel
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    api_key: Mapped[str] = mapped_column(unique=True, nullable=False)
    # Example field for usage limits
    limit: Mapped[int] = mapped_column(default=100)


engine = create_engine("sqlite:///./test.db", echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class UserCreate(BaseModel):
    username: str
    email: str
    api_key: str
