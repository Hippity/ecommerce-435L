from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.models.base import Base

class Wishlist(Base):
    """
    Wishlist model definition.

    Classes:
        Wishlist(Base): Represents a wishlist entry in the database.

    Attributes:
        wishlist_id (int): The unique identifier for the wishlist entry. Auto-incremented primary key.
        customer_id (int): The ID of the customer who added the item to their wishlist. 
                        Foreign key referencing the `customers` table.
        item_id (int): The ID of the inventory item added to the wishlist. 
                    Foreign key referencing the `inventory_item` table.
        created_at (datetime): The timestamp when the wishlist entry was created. Defaults to the current timestamp.

    Relationships:
        customer: A many-to-one relationship with the `Customer` model.
        inventory_item: A many-to-one relationship with the `InventoryItem` model.

    """
    __tablename__ = 'wishlist'
    wishlist_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)  
    item_id = Column(Integer, ForeignKey('inventory_item.id'), nullable=False) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())  

    # Relationships
    customer = relationship("Customer", back_populates="wishlist_items")  
    inventory_item = relationship("InventoryItem", back_populates="wishlist_items")
