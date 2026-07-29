"""
Base Model Module.
Why this file exists: Provides the declarative base class for all SQLAlchemy ORM models.
Why this design was chosen: Centralizing the base class allows Alembic to detect all models during migration generation.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
