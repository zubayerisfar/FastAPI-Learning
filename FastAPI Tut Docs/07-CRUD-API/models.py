from sqlalchemy import Column, Integer, String, Float
from db import base

class Item(base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    quantity = Column(Integer, default=0)
    
    