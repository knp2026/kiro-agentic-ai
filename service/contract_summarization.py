
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from transformers import pipeline

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/authenticate")
summarizer = pipeline("summarization")

@router.post("/summarize")
async def summarize_contract(contract_text: str, token: str = Depends(oauth2_scheme)):
    summary = summarizer(contract_text, max_length=130, min_length=30, do_sample=False)
    return {"summary": summary[0]["summary_text"]}