"""
Search API Router.
Why this file exists: Exposes the RAG query endpoint.
"""
from typing import Any
from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user import User
from app.schemas.search import SearchQuery, SearchResponse
from app.services.rag_service import query_documents

router = APIRouter()

@router.post("/query", response_model=SearchResponse)
def search_knowledge_base(
    query_in: SearchQuery,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Perform a semantic search over uploaded documents and generate an AI answer.
    """
    result = query_documents(user_id=current_user.id, query=query_in.query)
    
    return SearchResponse(
        answer=result["answer"],
        citations=result["citations"]
    )
