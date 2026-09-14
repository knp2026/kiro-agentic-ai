
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database import get_db
from models import Customer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/authenticate")

@router.post("/verify")
async def verify_customer(customer_id: str, db = Depends(get_db), token: str = Depends(oauth2_scheme)):
    customer = db.query(Customer).filter(Customer.CustomerID == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if customer.VerifiedStatus:
        return {"verified": True}
    else:
        return {"verified": False}