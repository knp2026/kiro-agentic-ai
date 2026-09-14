
from keycloak import KeycloakOpenID
from app.api.models import UserCredentials

keycloak_openid = KeycloakOpenID(server_url="http://keycloak:8080/",
                                  client_id="fastapi-client",
                                  realm_name="banking",
                                  client_secret_key="secret")

async def authenticate(user_credentials: UserCredentials):
    try:
        token = keycloak_openid.token(user_credentials.username, user_credentials.password)
        return token['access_token']
    except Exception as e:
        return None