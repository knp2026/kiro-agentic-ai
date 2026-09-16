
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import Customer
from auth import get_current_user

router = APIRouter()

@router.post("/verify")
async def verify_customer(customer_id: str, db=Depends(get_db), current_user: Customer = Depends(get_current_user)):
    if current_user.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this customer's data")
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if not customer.verified_status:
        raise HTTPException(status_code=401, detail="Customer not verified")
    return {"message": "Customer verified successfully"}