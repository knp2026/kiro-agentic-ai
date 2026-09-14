from pydantic import BaseModel

class AuthenticationRequest(BaseModel):
    username: str
    password: str

class AuthenticationResponse(BaseModel):
    access_token: str