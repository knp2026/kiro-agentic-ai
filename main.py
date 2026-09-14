
from fastapi import FastAPI
from app.api.controllers import auth_controller, contract_controller

app = FastAPI()

app.include_router(auth_controller.router, prefix="/auth", tags=["Authentication"])
app.include_router(contract_controller.router, prefix="/contracts", tags=["Contracts"])