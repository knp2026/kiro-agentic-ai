from fastapi import FastAPI

app = FastAPI()

# Import and include routers for each component
from routers import auth, verify, contract_retrieval, summarization

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(verify.router, prefix="/verify", tags=["Verification"])
app.include_router(contract_retrieval.router, prefix="/contracts", tags=["Contract Retrieval"])
app.include_router(summarization.router, prefix="/summarize", tags=["Summarization"])