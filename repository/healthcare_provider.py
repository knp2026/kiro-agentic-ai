
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class HealthcareProvider(Base):
    __tablename__ = 'healthcare_providers'

    provider_id = Column(Integer, primary_key=True)
    provider_name = Column(String)
    provider_type = Column(String)
    contact_information = Column(String)