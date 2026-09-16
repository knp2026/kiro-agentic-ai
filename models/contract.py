from pydantic import BaseModel, Field

class Contract(BaseModel):
    contract_id: str = Field(..., alias="ContractID")
    account_id: str = Field(..., alias="AccountID")
    contract_type: str = Field(..., alias="ContractType")

    class Config:
        allow_population_by_field_name = True