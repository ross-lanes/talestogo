import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get the absolute path of the project's root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the database URL for SQLite
# This ensures the path is always absolute, pointing to 'airo.db' in the project root
DATABASE_URL = f"sqlite:///{os.path.join(PROJECT_ROOT, 'airo.db')}"

# Create the SQLAlchemy engine
# connect_args is needed only for SQLite to allow it to be used by multiple threads
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class. Each instance of this class will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class. Your ORM models will inherit from this class.
Base = declarative_base()