from pydantic import BaseModel, Field,AnyUrl,EmailStr,field_validator,model_validator
from typing import List, Optional,Dict,Annotated,Any

class Person(BaseModel):
    """
    Basic Pydantic model with required fields.
    All fields are required by default in Pydantic.
    """
    name: str
    age: int
    email: EmailStr=None
    married:bool

    
    @field_validator("name")
    @classmethod
    def upper_name(cls,v:str) -> str:
        return v.upper()


    @model_validator(mode="after")
    def  validate_both(cls,model):
        if model.age >60 and model.email==None:
            raise ValueError("Old people must give backup email to contact")
        
