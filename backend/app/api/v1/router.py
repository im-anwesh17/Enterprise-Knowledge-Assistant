"""
API V1 Router.
Why this file exists: Combines all v1 API routers into a single router.
Why this design was chosen: Clean modular routing structure. Adding new feature routers in future phases will just be one line here.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, documents, search, sql_analytics, chat

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(sql_analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])



