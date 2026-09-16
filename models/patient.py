```python
from pydantic import BaseModel, EmailStr
from datetime import date

class Patient(BaseModel):
    PatientID: int
    FirstName: str
    LastName: str
    DateOfBirth: date
    Gender: str
    Phone: str
    Email: EmailStr
    Address: str
    EmergencyContactName: str
    EmergencyContactPhone: str
    EmergencyContactRelationship: str
```