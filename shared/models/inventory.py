from sqlalchemy import Column, Integer, String, Float
from shared.models.base import Base

class InventoryItem(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price_per_item = Column(Float, nullable=False)        
    description = Column(String, nullable=True)           
    stock_count = Column(Integer, nullable=False)          