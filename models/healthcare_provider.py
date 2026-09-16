```python
from pydantic import BaseModel, EmailStr

class HealthcareProvider(BaseModel):
    ProviderID: int
    ProviderName: str
    ProviderType: str
    Phone: str
    Email: EmailStr
    Address: str
```