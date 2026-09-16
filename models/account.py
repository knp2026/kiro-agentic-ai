from pydantic import BaseModel, Field

class Account(BaseModel):
    account_id: str = Field(..., alias="AccountID")
    customer_id: str = Field(..., alias="CustomerID")
    account_type: str = Field(..., alias="AccountType")
    account_number: str = Field(..., alias="AccountNumber")
    contracts: list[str] = Field(..., alias="Contracts")

    class Config:
        allow_population_by_field_name = True