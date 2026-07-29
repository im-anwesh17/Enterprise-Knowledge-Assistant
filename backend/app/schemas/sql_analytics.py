"""
SQL Analytics Schemas Module.
Why this file exists: Defines the request and response structure for the Text-to-SQL endpoint.
"""
from typing import List, Dict, Any
from pydantic import BaseModel

class NLQueryRequest(BaseModel):
    query: str

class SQLQueryResponse(BaseModel):
    generated_sql: str
    columns: List[str]
    results: List[Dict[str, Any]]
    explanation: str
