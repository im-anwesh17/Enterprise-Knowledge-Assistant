"""
SQL Analytics API Router.
Why this file exists: Exposes the Text-to-SQL functionality to the frontend.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.schemas.sql_analytics import NLQueryRequest, SQLQueryResponse
from app.core.db import get_db
from app.services.text_to_sql_service import generate_and_execute_sql

router = APIRouter()

@router.post("/text-to-sql", response_model=SQLQueryResponse)
def execute_nl_query(
    query_in: NLQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Translates a natural language question into SQL, safely executes it against the analytics data, and returns the result and explanation.
    """
    try:
        result = generate_and_execute_sql(db=db, question=query_in.query)
        return SQLQueryResponse(**result)
    except ValueError as ve:
        # Catch our custom security/parsing exceptions
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Catch unexpected LLM or DB errors
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
