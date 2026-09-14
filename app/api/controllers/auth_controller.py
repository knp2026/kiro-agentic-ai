
from fastapi import APIRouter, Depends, HTTPException
from app.api.models import UserCredentials
from app.api.services import auth_service

router = APIRouter()

@router.post("/authenticate")
async def authenticate(user_credentials: UserCredentials):
    access_token = await auth_service.authenticate(user_credentials)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": access_token}