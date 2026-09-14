
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from keycloak import KeycloakOpenID

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/authenticate")

keycloak_openid = KeycloakOpenID(server_url="http://keycloak:8080/",
                                  client_id="banking-service",
                                  realm_name="banking",
                                  client_secret_key="secret")

@router.post("/auth/authenticate")
async def authenticate(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        token = keycloak_openid.token(form_data.username, form_data.password)
        return {"access_token": token["access_token"]}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")