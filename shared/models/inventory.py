from sqlalchemy import Column, Integer, String, Float , Text
from shared.models.base import Base
from sqlalchemy.orm import relationship


class InventoryItem(Base):
    __tablename__ = 'inventory_item'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)
    price_per_item = Column(Float, nullable=False)
    description = Column(Text(400), nullable=True)
    stock_count = Column(Integer, nullable=False)

    reviews = relationship("Review", back_populates="inventory_item")
    orders = relationship("Order", back_populates="inventory_item")

    @classmethod
    def validate_data(cls, data):
        required_fields = ["name", "category", "price_per_item", "stock_count"]
        valid_categories = ["food", "clothes", "accessories", "electronics"]

        for field in required_fields:
            if field not in data:
                return False, f"'{field}' is a required field."

        if not isinstance(data["name"], str) or len(data["name"].strip()) < 3:
            return False, "Invalid value for 'name'. It must be at least 3 characters"

        if data["category"].lower() not in valid_categories:
            return False, f"Invalid value for 'category'. Valid options are: {', '.join(valid_categories)}."

        if not isinstance(data["price_per_item"], (int, float)) or data["price_per_item"] <= 0:
            return False, "Invalid value for 'price_per_item'. It must be a positive number."

        if not isinstance(data["stock_count"], int) or data["stock_count"] < 0:
            return False, "Invalid value for 'stock_count'. It must be a non-negative integer."

        if not isinstance(data["description"], str) or len(data["description"].strip()) < 5 :
            return False, "Invalid value for 'description'. It must be at least 5 characters."

        return True, "Validation successful."
