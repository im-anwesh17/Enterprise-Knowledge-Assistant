"""
Analytics Models Module.
Why this file exists: Defines the schema for business data that the Text-to-SQL engine will query.
Why this design was chosen: We need realistic demo data (Sales Analytics) so the LLM has a structured schema to parse and write queries against.
"""
from sqlalchemy import Column, Integer, String, Date, Numeric
from app.models.base import Base

class SalesAnalytics(Base):
    __tablename__ = "sales_analytics"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(100), nullable=False)
    product_category = Column(String(100), nullable=False)
    revenue = Column(Numeric(12, 2), nullable=False)
    units_sold = Column(Integer, nullable=False)
    sale_date = Column(Date, nullable=False)
    customer_segment = Column(String(100), nullable=False)
