"""
Chat Schemas Module.
Why this file exists: Defines the request and response shapes for the Conversational AI.
"""
from typing import List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.search import Citation

class ChatMessageCreate(BaseModel):
    content: str

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ChatAnswerResponse(BaseModel):
    answer: str
    citations: List[Citation]
