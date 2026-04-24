from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import sessionmaker, Session,DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker

engine=create_async_engine("sqlite+aiosqlite:///./test.db", connect_args={"check_same_thread": False})
SessionLocal=async_sessionmaker(autoflush=False, bind=engine)

# Base=declarative_base() # dont need anymore

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__="users"
    id=Column(Integer, primary_key=True, index=True)
    name=Column(String, index=True)
    email=Column(String, unique=True, index=True)
    
    
async def get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    db=SessionLocal()
    try:
        yield db
    finally:
        await db.close()
    
        

app=FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

@app.post("/users/", response_model=UserCreate)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@app.get("/users/")
async def read_users(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


