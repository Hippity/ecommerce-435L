from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from shared.models.base import Base

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)  
    item_id = Column(Integer, ForeignKey('inventory_item.id'), nullable=False) 
    good_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)  

    # Relationships
    customer = relationship("Customer", back_populates="previous_orders")  
    inventory_item = relationship("InventoryItem", back_populates="orders") 
