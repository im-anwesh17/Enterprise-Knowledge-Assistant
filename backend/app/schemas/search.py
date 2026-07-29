"""
Search Schemas Module.
Why this file exists: Defines structures for RAG queries and responses.
Why this design was chosen: Standardizing the response to include citations ensures the frontend can display exactly where the LLM got its information.
"""
from typing import List
from pydantic import BaseModel

class SearchQuery(BaseModel):
    query: str

class Citation(BaseModel):
    document_id: int
    filename: str
    page_number: int
    text_snippet: str

class SearchResponse(BaseModel):
    answer: str
    citations: List[Citation]
