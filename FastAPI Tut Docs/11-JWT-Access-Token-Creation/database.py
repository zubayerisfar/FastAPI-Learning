from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

DATABASE_URL = "sqlite:///./database.db"

engine= create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal= sessionmaker(autoflush=False, bind=engine)
