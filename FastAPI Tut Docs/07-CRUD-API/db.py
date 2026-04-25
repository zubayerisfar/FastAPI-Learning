import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# MySQL Connection Configuration
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "crud_api_db")

# Create MySQL connection URL
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# Create engine (echo=True shows SQL statements)
engine = create_engine(DATABASE_URL, echo=True)


class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
)
