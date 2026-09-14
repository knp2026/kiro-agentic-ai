from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, contracts, hitl

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
app.include_router(hitl.router, prefix="/hitl", tags=["hitl"])