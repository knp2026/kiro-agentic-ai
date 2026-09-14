
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from repository.base import Base

class Contract(Base):
    __tablename__ = 'contracts'

    contract_id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.account_id'))
    contract_type = Column(String)

    account = relationship('Account', back_populates='contracts')