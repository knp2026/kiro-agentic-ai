
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Consultation(Base):
    __tablename__ = 'consultations'

    consultation_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'))
    provider_id = Column(Integer, ForeignKey('healthcare_providers.provider_id'))