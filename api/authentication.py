
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db
from models import Customer
from auth import authenticate_customer, create_access_token

router = APIRouter()

@router.post("/authenticate")
async def authenticate(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    customer = await authenticate_customer(db, form_data.username, form_data.password)
    if not customer:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": customer.username})
    return {"access_token": access_token, "token_type": "bearer"}