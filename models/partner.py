```python
from pydantic import BaseModel, EmailStr

class Partner(BaseModel):
    PartnerID: int
    PartnerName: str
    PartnerType: str
    Phone: str
    Email: EmailStr
    Address: str
```