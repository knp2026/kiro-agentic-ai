
from fastapi import APIRouter, Depends, HTTPException
from services.contract_service import get_contracts_by_customer_id
from auth.keycloak_auth import verify_user

router = APIRouter()

@router.get("/contracts/{customer_id}")
async def get_contracts(customer_id: str, current_user: dict = Depends(verify_user)):
    contracts = get_contracts_by_customer_id(customer_id)
    if not contracts:
        raise HTTPException(status_code=404, detail="Contracts not found")
    return {"contracts": contracts}