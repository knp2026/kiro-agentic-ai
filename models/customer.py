from pydantic import BaseModel, EmailStr, Field
from datetime import date

class Customer(BaseModel):
    customer_id: str = Field(..., alias="CustomerID")
    first_name: str = Field(..., alias="FirstName")
    last_name: str = Field(..., alias="LastName")
    email: EmailStr = Field(..., alias="Email")
    phone_number: str = Field(..., alias="PhoneNumber")
    date_of_birth: date = Field(..., alias="DateOfBirth")
    account_numbers: list[str] = Field(..., alias="AccountNumbers")
    authentication_token: str = Field(..., alias="AuthenticationToken")
    verified_status: bool = Field(..., alias="VerifiedStatus")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }