
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'

    patient_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(Date)
    gender = Column(String)
    contact_information = Column(String)
    emergency_contact = Column(String)