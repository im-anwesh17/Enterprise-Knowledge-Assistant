"""
Seed Script Module.
Why this file exists: Initializes the database tables and creates the initial admin user.
Why this design was chosen: Running migrations directly via Alembic is safe, but we also need a way to populate data predictably on fresh deployments.
"""
import logging
from sqlalchemy.orm import Session
from app.core.db import engine, SessionLocal
from app.models.base import Base
from app.schemas.user import UserCreate
from app.repositories import user as crud_user
from app.models.analytics import SalesAnalytics
import app.models
from datetime import date
import random


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations, but we create them here as fallback
    Base.metadata.create_all(bind=engine)
    
    # Create Demo User
    demo_email = "admin@enterprise.com"
    user = crud_user.get_by_email(db, email=demo_email)
    if not user:
        user_in = UserCreate(
            email=demo_email,
            password="Admin@123",
            full_name="Enterprise Admin",
            is_active=True,
        )
        user = crud_user.create(db, obj_in=user_in)
        logger.info(f"Created demo user: {demo_email}")
    else:
        logger.info(f"Demo user {demo_email} already exists")

    # Seed Sales Analytics Data
    sales_count = db.query(SalesAnalytics).count()
    if sales_count == 0:
        logger.info("Seeding Sales Analytics data...")
        regions = ["North America", "Europe", "Asia Pacific"]
        categories = ["Software", "Hardware", "Services"]
        segments = ["Enterprise", "SMB", "Consumer"]
        
        for i in range(20):
            sale = SalesAnalytics(
                region=random.choice(regions),
                product_category=random.choice(categories),
                revenue=round(random.uniform(1000.0, 50000.0), 2),
                units_sold=random.randint(1, 100),
                sale_date=date(2023, random.randint(1, 12), random.randint(1, 28)),
                customer_segment=random.choice(segments)
            )
            db.add(sale)
        db.commit()
        logger.info("Seeded 20 mock sales records.")
    else:
        logger.info("Sales Analytics data already seeded.")

def main() -> None:
    logger.info("Creating initial data")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    logger.info("Initial data created")

if __name__ == "__main__":
    main()
