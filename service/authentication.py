
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

class TokenData(BaseModel):
    username: str | None = None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = keycloak_openid.decode_token(token)
        username: str = payload.get("preferred_username")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return TokenData(username=username)
    except:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@app.post("/auth/authenticate")
async def authenticate(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        token = keycloak_openid.token(form_data.username, form_data.password)
        return {"access_token": token["access_token"], "refresh_token": token["refresh_token"]}
    except:
        raise HTTPException(status_code=401, detail="Incorrect username or password")