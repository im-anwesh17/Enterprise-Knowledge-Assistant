"""
Chat Repositories Module.
Why this file exists: Abstracts database logic for ChatSessions and ChatMessages.
"""
from typing import List
from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.chat import ChatSession, ChatMessage

class CRUDChatSession(CRUDBase[ChatSession, dict, dict]):
    def get_by_user(self, db: Session, user_id: int) -> List[ChatSession]:
        return db.query(self.model).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()

class CRUDChatMessage(CRUDBase[ChatMessage, dict, dict]):
    def get_by_session(self, db: Session, session_id: int) -> List[ChatMessage]:
        return db.query(self.model).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()

chat_session = CRUDChatSession(ChatSession)
chat_message = CRUDChatMessage(ChatMessage)
