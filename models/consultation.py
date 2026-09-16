```python
from pydantic import BaseModel
from datetime import datetime

class Consultation(BaseModel):
    ConsultationID: int
    PatientID: int
    ProviderID: int
    AppointmentTime: datetime
```