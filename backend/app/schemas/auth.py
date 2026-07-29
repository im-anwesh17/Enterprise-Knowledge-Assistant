"""
Auth Schemas Module.
Why this file exists: Defines the data structures for Authentication API requests and responses.
Why this design was chosen: Pydantic schemas enforce type validation at the API boundary, automatically generating Swagger docs and rejecting invalid payloads.
"""
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str | None = None
