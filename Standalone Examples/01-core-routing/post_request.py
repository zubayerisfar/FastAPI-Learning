from pydantic import BaseModel,computed_field,Field
from typing import List, Optional,Literal,Annotated
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse


app = FastAPI()

class Patient(BaseModel):
    id : Annotated[str, Field(..., description="ID of the patient, must be a non-negative integer")]
    name: Annotated[str, Field(...,description="Name of the patient, must be between 1 and 50 characters long")]
    city: Annotated[str, Field(...,description="City where the patient is located, must be between 1 and 50 characters long")]
    age: Annotated[int, Field(ge=0,description="Age of the patient, must be a non-negative integer")]
    gender: Annotated[Literal["male", "female", "other"], Field(...,description="Gender of the patient, must be 'male', 'female', or 'other'")]
    height: Annotated[float, Field(gt=0,description="Height of the patient in meters, must be a non-negative float")]
    weight: Annotated[float, Field(gt=0,description="Weight of the patient in kilograms, must be a non-negative float")]

    @computed_field
    @property
    def bmi(self) -> float:
        return self.weight / (self.height ** 2)
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal weight"
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obesity"



def load_json():
    with open("basic_view.json") as f:
        return json.load(f)


def save_json(data):
    with open("basic_view.json", "w") as f:
        json.dump(data, f)

@app.get("/")
def index():
    return {"message": "Welcome to the Patient API. Use POST /patients to create a patient."}

@app.post("/create")
def create_patient(patient: Patient):
    data = load_json()

    if(patient.id in data):
        raise HTTPException(status_code=400,detail="Patient with this ID already exists")
    
    data[patient.id]=patient.model_dump(exclude=["id"])

    save_json(data)

    return JSONResponse(status_code=201, content={"message": "Patient created successfully"})