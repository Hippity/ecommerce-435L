from sqlalchemy import Column, Float, Integer, String 
from shared.models.base import Base

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False) 
    password = Column(String, nullable=False)            
    age = Column(Integer, nullable=False)
    address = Column(String, nullable=False)
    gender = Column(String, nullable=False)  
    marital_status = Column(String, nullable=False)     
    wallet = Column(Float, nullable=False, default=0.0)

    @classmethod
    def validate_data(cls, data):
        required_fields = ["fullname", "username", "password", "age", "address", "gender", "marital_status"]
        valid_genders = ["male", "female", "other"]
        valid_marital_statuses = ["single", "married"]

        for field in required_fields:
            if field not in data:
                return False, f"'{field}' is a required field."

        if not isinstance(data["fullname"], str) or  len(data["fullname"].strip()) < 4:
            return False, "Invalid value for 'fullname'. It must be at least 4 characters."

        if not isinstance(data["username"], str) or len(data["username"].strip()) < 4:
            return False, "Invalid value for 'username'. It must be at least 4 characters"

        if not isinstance(data["password"], str) or len(data["password"]) < 6:
            return False, "Invalid value for 'password'. It must be at least 6 characters long."

        if not isinstance(data["age"], int) or data["age"] < 16:
            return False, "Invalid value for 'age'. It must be greater than 16"

        if not isinstance(data["address"], str) or not len(data["address"].strip()) < 4:
            return False, "Invalid value for 'address'. It must be at least 4 characters"

        if data["gender"].lower() not in valid_genders:
            return False, f"Invalid value for 'gender'. Valid options are: {', '.join(valid_genders)}."

        if data["marital_status"].lower() not in valid_marital_statuses:
            return False, f"Invalid value for 'marital_status'. Valid options are: {', '.join(valid_marital_statuses)}."

        return True, "Validation successful."