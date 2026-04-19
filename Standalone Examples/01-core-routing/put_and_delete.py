from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Literal, Annotated
import json

app = FastAPI()

class Patient(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, ge=0)]
    gender: Annotated[Optional[Literal["male", "female", "other"]], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]

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


@app.put("/patients/{patient_id}")
def update(patient_id: str, patient: Patient):
    data = load_json()
    if(patient_id not in data):
        raise HTTPException(status_code=404, detail="Patient not found")
    
    existing_patient = data[patient_id]
    patient_json = patient.model_dump(exclude_unset=True)

    for key,value in patient_json.items():
        existing_patient[key] = value

    existing_patient["id"]=patient_id
    pydantic_converted=Patient(**existing_patient)
    modified_patient=pydantic_converted.model_dump(exclude=["id"])

    data[patient_id]=modified_patient

    save_json(data)

    return JSONResponse(status_code=200, content={"message": "Patient updated successfully"})

@app.delete("/patients/{patient_id}")
def delete(patient_id: str):
    data = load_json()
    if(patient_id not in data):
        raise HTTPException(status_code=404, detail="Patient not found")

    del data[patient_id]
    save_json(data)

    return JSONResponse(status_code=200, content={"message": "Patient deleted successfully"})