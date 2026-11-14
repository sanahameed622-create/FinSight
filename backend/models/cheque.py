from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class PostDatedCheque(Base):
    __tablename__ = "post_dated_cheques"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    cheque_number = Column(String(50), nullable=False, index=True)
    bank_name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    issue_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)  # Date on which cheque can be deposited
    status = Column(String(30), default="Pending Deposit")  # Pending Deposit, Deposited, Cleared, Bounced
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="cheques")
    customer = relationship("Customer", back_populates="cheques")
