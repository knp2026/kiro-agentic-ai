
from sqlalchemy.orm import Session
from models.contract import Contract
from schemas.contract import ContractCreate

def get_contract_by_id(db: Session, contract_id: int):
    return db.query(Contract).filter(Contract.ContractID == contract_id).first()

def get_contracts_by_account_id(db: Session, account_id: int):
    return db.query(Contract).filter(Contract.AccountID == account_id).all()

def create_contract(db: Session, contract: ContractCreate):
    db_contract = Contract(**contract.dict())
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract