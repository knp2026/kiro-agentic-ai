
from fastapi import APIRouter, Depends, HTTPException
from app.api.models import ContractRequest, ContractResponse
from app.api.services import contract_service, auth_service

router = APIRouter()

@router.post("/retrieve", response_model=ContractResponse)
async def retrieve_contract(request: ContractRequest, current_user: dict = Depends(auth_service.get_current_user)):
    contract = await contract_service.retrieve_contract(current_user["customer_id"], request.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractResponse(contract_content=contract)