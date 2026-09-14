
from sqlalchemy.orm import Session
from models.account import Account
from schemas.account import AccountCreate

def get_account(db: Session, account_id: int):
    return db.query(Account).filter(Account.AccountID == account_id).first()

def get_accounts_by_customer_id(db: Session, customer_id: int):
    return db.query(Account).filter(Account.CustomerID == customer_id).all()

def create_account(db: Session, account: AccountCreate):
    db_account = Account(**account.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account