
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import psycopg2

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class VerificationRequest(BaseModel):
    customer_id: str

def get_db_connection():
    conn = psycopg2.connect(database="banking", user="postgres", password="postgres", host="postgres", port="5432")
    return conn

@app.post("/verify", response_model=dict)
async def verify_customer(request: VerificationRequest, current_user: str = Depends(oauth2_scheme)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT VerifiedStatus FROM Customer WHERE CustomerID = %s", (request.customer_id,))
    result = cur.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    if result[0] == "Verified":
        return {"verification_status": "Verified"}
    else:
        return {"verification_status": "Not Verified"}