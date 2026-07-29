"""
User Schemas Module.
Why this file exists: Defines the API representations of a User.
Why this design was chosen: Separating UserCreate from UserResponse ensures we never accidentally leak password hashes in API responses.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
