
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Consent
from schemas import ConsentCreate, Consent as ConsentSchema

router = APIRouter()

@router.post("/", response_model=ConsentSchema)
def create_consent(consent: ConsentCreate, db: Session = Depends(get_db)):
    db_consent = Consent(**consent.dict())
    db.add(db_consent)
    db.commit()
    db.refresh(db_consent)
    return db_consent

# Add more endpoints for read, update, delete operations