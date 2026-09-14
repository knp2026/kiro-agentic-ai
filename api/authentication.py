
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from auth.keycloak_auth import authenticate_user, verify_user

router = APIRouter()

@router.post("/authenticate")
async def authenticate(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"access_token": user.access_token}

@router.post("/verify")
async def verify(customer_id: str, current_user: dict = Depends(verify_user)):
    # Implementation for customer verification
    return {"verified": True}