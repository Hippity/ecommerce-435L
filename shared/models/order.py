from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from shared.models.base import Base
from sqlalchemy.sql import func

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)  
    item_id = Column(Integer, ForeignKey('inventory_item.id'), nullable=False) 
    quantity = Column(Integer, nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())  

    # Relationships
    customer = relationship("Customer", back_populates="previous_orders")  
    inventory_item = relationship("InventoryItem", back_populates="orders") 
