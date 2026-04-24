from pydantic import BaseModel, Field,AnyUrl,EmailStr
from typing import List, Optional,Dict,Annotated,Any

class Person(BaseModel):
    """
    Basic Pydantic model with required fields.
    All fields are required by default in Pydantic.
    """
    name: str
    age: int
    married:bool

class Person1(BaseModel):
    """
    Adds a default value to 'married'.
    Fields with default values become optional in the schema.
    """
    name: str
    age: int
    married: bool = False

class Person2(BaseModel):
    """
    Uses Field for validation:
    - name: must be 1-50 chars
    - age: must be >= 0
    - married: default False
    Field(...) means required with extra validation.
    """
    name: str=Field(..., min_length=1, max_length=50)
    age: int=Field(..., ge=0)
    married: bool = Field(default=False)


class Person3(BaseModel):
    """
    Adds:
    - hobbies: List[str], default None
    - contract: Dict[str, str], default None
    Shows how to use typing for complex fields.
    """
    name: str=Field(..., min_length=1, max_length=50)
    age: int=Field(..., ge=0)
    hobbies=List(str)=None
    contract=Dict[str,str]=None
    married: bool = Field(default=False)

class Person4(BaseModel):
    """
    Uses Annotated for type + validation + description.
    - default_factory for mutable defaults (list, dict)
    - Field descriptions show up in OpenAPI/docs
    """
    name:Annotated[str, Field(..., min_length=1, max_length=50, description="The person's name")]
    age:Annotated[int, Field(..., ge=0, description="The person's age")]
    hobbies:Annotated[List[str], Field(default_factory=list, description="List of hobbies")]
    contract:Annotated[Dict[str,str], Field(default_factory=dict, description="Contract details")]
    married:Annotated[bool, Field(default=False, description="Is the person married?")]

class Person5(BaseModel):
    """
    Adds Optional field:
    - earning: float, must be >0 if provided, else None
    Shows how to use Optional with Annotated and Field.
    """
    name:Annotated[str, Field(..., min_length=1, max_length=50, description="The person's name")]
    age:Annotated[int, Field(..., ge=0, description="The person's age")]
    hobbies:Annotated[List[str], Field(default_factory=list, description="List of hobbies")]
    contract:Annotated[Dict[str,str], Field(default_factory=dict, description="Contract details")]
    earning:Optional[Annotated[float, Field(gt=0, description="Earning amount")]]=None #optional gives flexibility of not providing this field
    married:Annotated[bool, Field(default=False, description="Is the person married?")]


class Person6(BaseModel):
    """
    Adds 'strict=True' to age:
    - Only accepts real integers (not float/str that can be cast)
    - Useful for strict data validation
    """
    name:Annotated[str, Field(..., min_length=1, max_length=50, description="The person's name")]
    age:Annotated[int, Field(..., ge=0, strict=True, description="The person's age")] # strict ensures only integer value submission
    hobbies:Annotated[List[str], Field(default_factory=list, description="List of hobbies")]
    contract:Annotated[Dict[str,str], Field(default_factory=dict, description="Contract details")]
    earning:Optional[Annotated[float, Field(gt=0, description="Earning amount")]]=None #optional gives flexibility of not providing this field
    married:Annotated[bool, Field(default=False, description="Is the person married?")]


