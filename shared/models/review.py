from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.models.base import Base

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_username = Column(Integer, ForeignKey('customers.username'), nullable=False)  
    item_id = Column(Integer, ForeignKey('inventory_items.id'), nullable=False)  
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)  
    status = Column(Text, nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())  
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 

    customer = relationship("Customer", back_populates="reviews")
    product = relationship("InventoryItem", back_populates="reviews")

