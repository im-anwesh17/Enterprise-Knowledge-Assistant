"""
Chat API Router.
Why this file exists: Exposes conversational memory endpoints.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.chat import ChatSession
from app.schemas.chat import ChatMessageCreate, ChatSessionResponse, ChatAnswerResponse
from app.core.db import get_db
from app.repositories import chat as crud_chat
from app.services.chat_service import conversational_rag

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    title: str = "New Chat",
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Create a new chat session."""
    session = ChatSession(user_id=current_user.id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get all chat sessions for user."""
    return crud_chat.chat_session.get_by_user(db=db, user_id=current_user.id)

@router.post("/sessions/{session_id}/message", response_model=ChatAnswerResponse)
def send_message(
    session_id: int,
    message_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Send a message to a session and get an AI response with memory."""
    session = crud_chat.chat_session.get(db=db, id=session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = conversational_rag(
        db=db, 
        user_id=current_user.id, 
        session_id=session_id, 
        query=message_in.content
    )
    
    return ChatAnswerResponse(**result)
