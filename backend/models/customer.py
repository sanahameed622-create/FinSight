from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    company_name = Column(String(150), nullable=True)
    phone = Column(String(30), nullable=False)
    email = Column(String(100), nullable=True)
    city = Column(String(50), default="Lahore")
    address = Column(String(255), nullable=True)
    ntn_number = Column(String(50), nullable=True)
    credit_limit = Column(Float, default=100000.0)
    payment_terms_days = Column(Integer, default=15)
    current_balance = Column(Float, default=0.0)  # Total unpaid balance
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    cheques = relationship("PostDatedCheque", back_populates="customer", cascade="all, delete-orphan")
