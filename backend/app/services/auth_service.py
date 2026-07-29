"""
Auth Service Module.
Why this file exists: Contains the business logic for authentication (verifying credentials and generating tokens).
Why this design was chosen: Separation of concerns. The router should only handle HTTP, while the service handles business logic.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password
from app.repositories import user as crud_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = crud_user.get_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
