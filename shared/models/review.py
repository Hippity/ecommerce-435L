from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.models.base import Base

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)  
    item_id = Column(Integer, ForeignKey('inventory_item.id'), nullable=False)  
    rating = Column(Integer, nullable=False)
    comment = Column(Text(400), nullable=True)  
    status = Column(String(50), nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())  
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 

    customer = relationship("Customer", back_populates="reviews")
    inventory_item = relationship("InventoryItem", back_populates="reviews")
    
    @classmethod
    def validate_data(cls, data):

        required_fields = ["rating"]
        valid_statuses = ["approved", "normal" ,"flagged"]

        # Check for missing fields
        for field in required_fields:
            if field not in data:
                return False, f"'{field}' is a required field."

        if not isinstance(data["rating"], int) or not (1 <= data["rating"] <= 5):
            return False, "Invalid rating. Must be an integer between 1 and 5."

        if "comment" in data and not isinstance(data["comment"], (str, type(None))):
            return False, "Invalid comment. Must be a string or null."

        if "status" in data and data["status"].lower() not in valid_statuses:
            return False, f"Invalid status. Valid options are: {', '.join(valid_statuses)}."

        return True, "Validation successful."
