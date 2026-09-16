
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import Customer, Account, Contract
from auth import get_current_user
from summarization import summarize_contract

router = APIRouter()

@router.get("/summarize/{contract_id}")
async def summarize_contract_endpoint(contract_id: str, db=Depends(get_db), current_user: Customer = Depends(get_current_user)):
    contract = db.query(Contract).filter(Contract.contract_id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    account = db.query(Account).filter(Account.account_id == contract.account_id).first()
    if not account or account.customer_id != current_user.customer_id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this contract")
    summary = summarize_contract(contract.contract_content)
    return {"summary": summary}