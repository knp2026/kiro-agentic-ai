
from sqlalchemy.orm import Session
from models.customer import Customer
from schemas.customer import CustomerCreate

def get_customer_by_id(db: Session, customer_id: int):
    return db.query(Customer).filter(Customer.CustomerID == customer_id).first()

def get_customer_by_email(db: Session, email: str):
    return db.query(Customer).filter(Customer.Email == email).first()

def create_customer(db: Session, customer: CustomerCreate):
    db_customer = Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer