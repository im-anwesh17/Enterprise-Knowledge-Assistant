"""
User Repository Module.
Why this file exists: Provides User-specific database operations.
Why this design was chosen: Encapsulates complex DB logic (like fetching a user by email or hashing a password before creation) away from routers or services.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserBase
from app.core.security import get_password_hash

class CRUDUser(CRUDBase[User, UserCreate, UserBase]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

user = CRUDUser(User)
