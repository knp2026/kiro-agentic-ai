from pydantic import BaseModel
from datetime import date

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    contact_information: str
    emergency_contact: str

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int

    class Config:
        orm_mode = True