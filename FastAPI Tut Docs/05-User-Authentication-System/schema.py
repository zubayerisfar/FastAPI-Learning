from pydantic import BaseModel

class Register(BaseModel):
    username:str
    age:int
    password:str
    
class Login(BaseModel):
    username:str
    password:str
    
