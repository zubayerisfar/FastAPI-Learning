from pydantic import BaseModel,EmailStr,computed_field
from typing import List,Dict


from fastapi import FastAPI

app=FastAPI()

class Model(BaseModel):
    name:str
    age:int
    height=float
    weight=float

    @computed_field
    @property
    def bmi(self)-> float:
        bmi= self.weight/self.height**2
        return bmi

