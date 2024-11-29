from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.models.base import Base

class Wishlist(Base):
    __tablename__ = 'wishlist'
    wishlist_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)  
    item_id = Column(Integer, ForeignKey('inventory_item.id'), nullable=False) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())  

    # Relationships
    customer = relationship("Customer", back_populates="wishlist_items")  
    inventory_item = relationship("InventoryItem", back_populates="wishlist_items")
