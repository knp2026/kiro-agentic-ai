
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from auth.keycloak_auth import get_current_user
from services.customer_service import verify_customer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/authentication/authenticate")

@router.post("/verify")
async def verify_customer_endpoint(customer_id: str, token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    verified = verify_customer(customer_id)
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer verification failed",
        )
    return {"verification_status": "success"}