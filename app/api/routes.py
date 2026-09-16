
from fastapi import APIRouter
from app.api.controllers import authentication_controller, contract_controller

router = APIRouter()
router.include_router(authentication_controller.router, prefix="/auth", tags=["Authentication"])
router.include_router(contract_controller.router, prefix="/contracts", tags=["Contracts"])