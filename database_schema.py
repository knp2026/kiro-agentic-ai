
from sqlalchemy import Column, UUID, String, Date, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Patient Entity
class Patient(Base):
    __tablename__ = 'Patient'

    PatientID = Column(UUID, primary_key=True)
    FirstName = Column(String(255), nullable=False)
    LastName = Column(String(255), nullable=False)
    DateOfBirth = Column(Date, nullable=False)
    Gender = Column(String(50), nullable=False)
    ContactInformation = Column(JSON, nullable=False)
    EmergencyContact = Column(JSON, nullable=False)

# HealthcareProvider Entity
class HealthcareProvider(Base):
    __tablename__ = 'HealthcareProvider'

    ProviderID = Column(UUID, primary_key=True)
    ProviderName = Column(String(255), nullable=False)
    ProviderType = Column(String(255), nullable=False)
    ContactInformation = Column(JSON, nullable=False)

# Partner Entity
class Partner(Base):
    __tablename__ = 'Partner'

    PartnerID = Column(UUID, primary_key=True)
    PartnerName = Column(String(255), nullable=False)
    PartnerType = Column(String(255), nullable=False)
    ContactInformation = Column(JSON, nullable=False)

# Consultation Entity
class Consultation(Base):
    __tablename__ = 'Consultation'

    ConsultationID = Column(UUID, primary_key=True)
    PatientID = Column(UUID, ForeignKey('Patient.PatientID'))
    ProviderID = Column(UUID, ForeignKey('HealthcareProvider.ProviderID'))