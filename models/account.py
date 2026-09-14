from pydantic import BaseModel
from typing import List

class Account(BaseModel):
    AccountID: int
    CustomerID: int
    AccountType: str
    AccountNumber: str
    Contracts: List[int]