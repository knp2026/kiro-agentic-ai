
from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy.orm import relationship
from repository.base import Base

class Customer(Base):
    __tablename__ = 'customers'

    customer_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String)
    date_of_birth = Column(Date)
    authentication_token = Column(String)
    verified_status = Column(Boolean)

    accounts = relationship('Account', back_populates='customer')