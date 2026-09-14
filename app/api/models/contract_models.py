
from pydantic import BaseModel

class ContractRequest(BaseModel):
    contract_id: str

class ContractResponse(BaseModel):
    contract_content: str