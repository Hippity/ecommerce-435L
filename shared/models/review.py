from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.models.base import Base

class Review(Base):
    """
    Review model definition and validation.

    Classes:
        Review(Base): Represents a review in the database.

    Attributes:
        id (int): The unique identifier for the review. Auto-incremented primary key.
        customer_id (int): The ID of the customer who wrote the review. Foreign key referencing the `customers` table.
        item_id (int): The ID of the inventory item being reviewed. Foreign key referencing the `inventory_item` table.
        rating (int): The rating given by the customer. Must be an integer between 1 and 5.
        comment (str): Optional comment provided by the customer.
        status (str): The status of the review. Valid options: "approved", "normal", "flagged".
        created_at (datetime): The timestamp when the review was created. Defaults to the current timestamp.
        updated_at (datetime): The timestamp when the review was last updated. Automatically updated.

    Relationships:
        customer: A many-to-one relationship with the `Customer` model.
        inventory_item: A many-to-one relationship with the `InventoryItem` model.

    Methods:
        validate_data(data):
            Validates review data against required fields and constraints.
    """
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
        """
            Validates review data.

            Parameters:
                data (dict): A dictionary containing review data to validate.

            Returns:
                tuple: A boolean indicating success (True) or failure (False), and a message.

            Validation Rules:
                - `rating` (required): Must be an integer between 1 and 5.
                - `comment` (optional): Must be a string or null.
                - `status` (optional): Must be one of "approved", "normal", or "flagged".
        """
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
