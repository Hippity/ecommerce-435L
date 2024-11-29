from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Fetch the database connection URL from the environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Create a SQLAlchemy engine instance to manage the connection to the database
# The `echo=True` parameter enables logging of SQL queries for debugging purposes
engine = create_engine(DATABASE_URL, echo=True)

# Create a session factory bound to the database engine
# - `autocommit=False`: Disables automatic commit of transactions, giving more control over database operations.
# - `autoflush=False`: Disables automatic flushing of changes to the database to avoid unexpected behaviors.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
