
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import keycloak

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    username: str | None = None

def get_keycloak_admin():
    server_url = "http://keycloak:8080/"
    admin_username = "admin"
    admin_password = "admin"
    realm_name = "banking"
    keycloak_admin = keycloak.KeycloakAdmin(server_url=server_url, username=admin_username, password=admin_password, realm_name=realm_name, verify=True)
    return keycloak_admin

@app.post("/token", response_model=TokenData)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    keycloak_admin = get_keycloak_admin()
    try:
        token = keycloak_admin.obtain_token(username=form_data.username, password=form_data.password)
        return {"access_token": token['access_token'], "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

@app.get("/users/me", response_model=TokenData)
async def read_users_me(current_user: TokenData = Depends(oauth2_scheme)):
    return current_user