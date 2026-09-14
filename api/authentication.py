
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from keycloak import KeycloakOpenID

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

keycloak_openid = KeycloakOpenID(server_url="http://keycloak:8080/",
                                  client_id="banking-service",
                                  realm_name="banking",
                                  client_secret_key="secret")

class Token(BaseModel):
    access_token: str
    refresh_token: str

@app.post("/auth/authenticate", response_model=Token)
async def authenticate(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        token = keycloak_openid.token(form_data.username, form_data.password)
        return {"access_token": token['access_token'], "refresh_token": token['refresh_token']}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Incorrect username or password")