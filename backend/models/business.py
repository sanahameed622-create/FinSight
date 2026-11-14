from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    registration_no = Column(String(50), nullable=True)  # NTN / STRN
    phone = Column(String(30), nullable=True)
    city = Column(String(50), default="Lahore")
    address = Column(String(255), nullable=True)
    currency = Column(String(10), default="PKR")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="business")
    customers = relationship("Customer", back_populates="business", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="business", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="business", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="business", cascade="all, delete-orphan")
    cheques = relationship("PostDatedCheque", back_populates="business", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="business", cascade="all, delete-orphan")
