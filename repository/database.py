
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .patient import Base as PatientBase
from .healthcare_provider import Base as HealthcareProviderBase
from .partner import Base as PartnerBase
from .consultation import Base as ConsultationBase

DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

PatientBase.metadata.create_all(bind=engine)
HealthcareProviderBase.metadata.create_all(bind=engine)
PartnerBase.metadata.create_all(bind=engine)
ConsultationBase.metadata.create_all(bind=engine)