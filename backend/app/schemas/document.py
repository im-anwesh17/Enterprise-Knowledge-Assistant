"""
Document Schemas Module.
Why this file exists: Defines API input/output structures for documents.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    chunk_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
