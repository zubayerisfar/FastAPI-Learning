from sqlalchemy.orm import sessionmaker,DeclarativeBase,Mapped,mapped_column
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy import Integer, create_engine

# Database setup
class Base(DeclarativeBase):
    pass

class LogUser(Base):
    __tablename__ = "log_users"
    id = mapped_column(Integer, primary_key=True, index=True)
    username = mapped_column(String(50), unique=True, index=True)
    email = mapped_column(String(100), unique=True, index=True)
    

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/log_users_db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autoflush=False, bind=engine)

def create_db_and_tables():
    Base.metadata.create_all(engine)
