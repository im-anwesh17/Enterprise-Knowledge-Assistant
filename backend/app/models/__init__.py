"""
Models Init Module.
Why this file exists: To import all models in one place.
Why this design was chosen: Alembic needs to import all models before it can auto-generate migrations by comparing metadata to the database.
"""
from app.models.base import Base
from app.models.user import User
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.models.analytics import SalesAnalytics

