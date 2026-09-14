from pydantic import BaseModel
from typing import List

class Customer(BaseModel):
    CustomerID: int
    FirstName: str
    LastName: str
    Email: str
    PhoneNumber: str
    DateOfBirth: str
    AccountNumbers: List[int]
    AuthenticationToken: str
    VerifiedStatus: bool