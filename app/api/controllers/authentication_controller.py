
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.services import authentication_service
from app.api.models import AuthenticationRequest, AuthenticationResponse

router = APIRouter()

@router.post("/authenticate", response_model=AuthenticationResponse)
async def authenticate(request: AuthenticationRequest):
    try:
        access_token = await authentication_service.authenticate(request.username, request.password)
        return AuthenticationResponse(access_token=access_token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))