from pydantic import BaseModel, Field,AnyUrl,EmailStr,field_validator
from typing import List, Optional,Dict,Annotated,Any

class Person(BaseModel):
    """
    Basic Pydantic model with required fields.
    All fields are required by default in Pydantic.
    """
    name: str
    age: int
    email: EmailStr
    married:bool

    
    @field_validator("name")
    @classmethod
    def upper_name(cls,v:str) -> str:
        return v.upper()


    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v:
            raise ValueError('Name must not be empty')
        return v


    @field_validator('email')
    @classmethod
    def validate_email(cls, v: EmailStr) -> EmailStr:
        allowed_domains = ['example.com', 'test.com']
        domain = v.split('@')[-1] #get the last value after splitting
        if domain not in allowed_domains:
            raise ValueError(f'Email domain must be one of: {allowed_domains}')
        return v
    
    @field_validator('name',mode="before")
    @classmethod
    def validate_name_before(cls, v: str) -> str:
        if not v:
            raise ValueError('Name must not be empty')
        return v