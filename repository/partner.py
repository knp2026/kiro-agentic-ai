
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Partner(Base):
    __tablename__ = 'partners'

    partner_id = Column(Integer, primary_key=True)
    partner_name = Column(String)
    partner_type = Column(String)
    contact_information = Column(String)