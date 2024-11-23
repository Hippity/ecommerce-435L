from sqlalchemy import Column, Float, Integer, String 
from shared.models.base import Base

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False) 
    password = Column(String, nullable=False)            
    age = Column(Integer, nullable=False)
    address = Column(String, nullable=False)
    gender = Column(String, nullable=False)  
    marital_status = Column(String, nullable=False)     
    wallet = Column(Float, nullable=False, default=0.0)