from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    sku = Column(String(50), index=True, nullable=False)
    name = Column(String(150), nullable=False)
    category = Column(String(80), default="General")
    unit = Column(String(30), default="Carton")
    stock_quantity = Column(Float, default=0.0)
    unit_cost = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    reorder_level = Column(Float, default=10.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="products")
