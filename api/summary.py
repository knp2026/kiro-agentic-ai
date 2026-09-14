
from fastapi import APIRouter, Depends, HTTPException
from services.summary_service import summarize_contract
from auth.keycloak_auth import verify_user

router = APIRouter()

@router.get("/summary/{contract_id}")
async def get_summary(contract_id: str, current_user: dict = Depends(verify_user)):
    summary = summarize_contract(contract_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return {"summary": summary}