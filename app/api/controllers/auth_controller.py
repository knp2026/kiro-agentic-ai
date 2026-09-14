```python
from fastapi import APIRouter, Depends, HTTPException
from app.api.services import auth_service
from app.api.models import AuthRequest, AuthResponse

router = APIRouter()

@router.post("/authenticate", response_model=AuthResponse)
async def authenticate(request: AuthRequest):
    user = await auth_service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth_service.generate_access_token(user)
    return AuthResponse(access_token=access_token)
```