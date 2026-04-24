from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

base = declarative_base()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
)
