from pydantic import BaseModel, Field

class Contract(BaseModel):
    contract_id: str = Field(..., alias='ContractID')
    account_id: str = Field(..., alias='AccountID')
    contract_type: str = Field(..., alias='ContractType')