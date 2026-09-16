from pydantic import BaseModel

class Patient(BaseModel):
    firstName: str
    lastName: str
    dateOfBirth: str
    gender: str
    email: str
    phone: str
    address: dict
    partnerId: str

class Consent(BaseModel):
    patientId: int
    partnerId: str
    consentType: str
    consentDate: str

class Appointment(BaseModel):
    patientId: int
    providerId: str
    appointmentDate: str
    appointmentTime: str