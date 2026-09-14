
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from repository.base import Base

class Account(Base):
    __tablename__ = 'accounts'

    account_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    account_type = Column(String)
    account_number = Column(String, unique=True)

    customer = relationship('Customer', back_populates='accounts')
    contracts = relationship('Contract', back_populates='account')