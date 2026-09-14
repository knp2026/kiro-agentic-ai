from pydantic import BaseModel

class Contract(BaseModel):
    ContractID: int
    AccountID: int
    ContractType: str