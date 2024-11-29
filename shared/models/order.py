from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from shared.models.base import Base
from sqlalchemy.sql import func

class Order(Base):
    """
    Order model definition.
    
    Classes:
        Order(Base): Represents an order in the database.

    Attributes:
        id (int): The unique identifier for the order. Auto-incremented primary key.
        customer_id (int): The ID of the customer who placed the order. Foreign key referencing the `customers` table.
        item_id (int): The ID of the inventory item ordered. Foreign key referencing the `inventory_item` table.
        quantity (int): The number of units ordered. Must be a positive integer.
        created_at (datetime): The timestamp when the order was created. Defaults to the current timestamp.

    Relationships:
        customer: A many-to-one relationship with the `Customer` model.
        inventory_item: A many-to-one relationship with the `InventoryItem` model.
"""
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)  
    item_id = Column(Integer, ForeignKey('inventory_item.id'), nullable=False) 
    quantity = Column(Integer, nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())  

    # Relationships
    customer = relationship("Customer", back_populates="previous_orders")  
    inventory_item = relationship("InventoryItem", back_populates="orders") 
