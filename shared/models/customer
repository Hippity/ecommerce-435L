from sqlalchemy import Column, Float, Integer, String 
from sqlalchemy.orm import relationship
from shared.models.base import Base
from shared.models.order import Order  # Import the Order class

class Customer(Base):
    """
    Customer model definition and validation.

    Classes:
        Customer(Base): Represents a customer in the database.

    Attributes:
        id (int): The unique identifier for the customer. Auto-incremented primary key.
        fullname (str): The full name of the customer. Required, minimum 4 characters.
        username (str): The unique username of the customer. Required, minimum 4 characters.
        password (str): The hashed password of the customer. Required, minimum 6 characters.
        age (int): The age of the customer. Must be greater than 16.
        address (str): The address of the customer. Required, minimum 4 characters.
        gender (str): The gender of the customer. Valid values: "male", "female", "other".
        marital_status (str): The marital status of the customer. Valid values: "single", "married".
        wallet (float): The wallet balance of the customer. Defaults to 0.0.
        role (str): The role of the customer. Defaults to "customer".

    Relationships:
        reviews: A one-to-many relationship with the `Review` model.
        previous_orders: A one-to-many relationship with the `Order` model.
        wishlist_items: A one-to-many relationship with the `Wishlist` model.

    Methods:
        validate_data(data, type): Validates the customer data against the required fields and constraints.
    """
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String(100), nullable=False)  
    username = Column(String(50), unique=True, nullable=False)  
    password = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    address = Column(String(255), nullable=False) 
    gender = Column(String(10), nullable=False) 
    marital_status = Column(String(10), nullable=False) 
    wallet = Column(Float, nullable=False, default=0.0)
    role = Column(String(100), default="customer")

    reviews = relationship("Review", back_populates="customer")
    previous_orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    wishlist_items = relationship("Wishlist", back_populates="customer")

    @classmethod
    def validate_data(cls, data,type):
        """
        Validates customer data.

        Parameters:
            data (dict): A dictionary containing customer data to validate.
            type (str): The validation context, either "edit" (for updates) or any other value (for creation).

        Returns:
            tuple: A boolean indicating success (True) or failure (False), and a message.

        Validation Rules:
            - All required fields must be present.
            - `fullname`, `username`, `address`: Must be strings with a minimum length of 4 characters.
            - `password`: Must be a string with a minimum length of 6 characters.
            - `age`: Must be an integer greater than 16.
            - `gender`: Must be one of "male", "female", "other".
            - `marital_status`: Must be one of "single", "married".
        """
        required_fields = ["fullname", "username", "password", "age", "address", "gender", "marital_status"]
        if type == "edit":
            required_fields = ["fullname", "age", "address", "gender", "marital_status"]

        valid_genders = ["male", "female", "other"]
        valid_marital_statuses = ["single", "married"]

        for field in required_fields:
            if field not in data:
                return False, f"'{field}' is a required field."

        if "fullname" in data:
            if not isinstance(data["fullname"], str) or len(data["fullname"].strip()) < 4:
                return False, "Invalid value for 'fullname'. It must be at least 4 characters."

        if "username" in data:
            if not isinstance(data["username"], str) or len(data["username"].strip()) < 4:
                return False, "Invalid value for 'username'. It must be at least 4 characters."

        if "password" in data:
            if not isinstance(data["password"], str) or len(data["password"]) < 6:
                return False, "Invalid value for 'password'. It must be at least 6 characters long."

        if "age" in data:
            if not isinstance(data["age"], int) or data["age"] < 16:
                return False, "Invalid value for 'age'. It must be greater than 16."

        if "address" in data:
            if not isinstance(data["address"], str) or len(data["address"].strip()) < 4:
                return False, "Invalid value for 'address'. It must be at least 4 characters."

        if "gender" in data:
            if data["gender"].lower() not in valid_genders:
                return False, f"Invalid value for 'gender'. Valid options are: {', '.join(valid_genders)}."

        if "marital_status" in data:
            if data["marital_status"].lower() not in valid_marital_statuses:
                return False, f"Invalid value for 'marital_status'. Valid options are: {', '.join(valid_marital_statuses)}."

        if "wallet" in data:  # Example of an optional field
            if not isinstance(data["wallet"], (int, float)) or data["wallet"] < 0:
                return False, "Invalid value for 'wallet'. It must be a non-negative number."

        return True, "Validation successful."