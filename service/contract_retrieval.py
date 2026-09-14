
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database import get_db
from models import Account, Contract

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/authenticate")

@router.get("/contracts/{account_id}")
async def get_contracts(account_id: str, db = Depends(get_db), token: str = Depends(oauth2_scheme)):
    account = db.query(Account).filter(Account.AccountID == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    contracts = db.query(Contract).filter(Contract.AccountID == account_id).all()
    return {"contracts": [contract.dict() for contract in contracts]}