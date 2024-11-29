from sqlalchemy.ext.declarative import declarative_base

# Create a base class for all ORM (Object-Relational Mapping) models.
# This base class will be used to define database tables as Python classes.
# It provides metadata and methods that SQLAlchemy uses to interact with the database.
Base = declarative_base()
