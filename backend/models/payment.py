from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    payment_number = Column(String(50), unique=True, index=True, nullable=False)
    payment_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    unallocated_amount = Column(Float, nullable=False)
    payment_method = Column(String(50), default="Bank Transfer")  # Bank Transfer, Raast, Cash, Cheque, Pay Order
    reference_number = Column(String(100), nullable=True)
    bank_name = Column(String(100), nullable=True)
    status = Column(String(30), default="Unallocated")  # Unallocated, Partially Allocated, Fully Reconciled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")
