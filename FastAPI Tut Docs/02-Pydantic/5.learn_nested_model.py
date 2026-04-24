from pydantic import BaseModel

class Address(BaseModel):
    city:str
    road:str
    building_no:str


class Information(BaseModel):
    name:str
    age:str
    address=Address

