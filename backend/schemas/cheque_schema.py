from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ChequeBase(BaseModel):
    customer_id: int
    cheque_number: str
    bank_name: str
    amount: float
    issue_date: date
    maturity_date: date
    status: Optional[str] = "Pending Deposit"
    notes: Optional[str] = None

class ChequeCreate(ChequeBase):
    pass

class ChequeStatusUpdate(BaseModel):
    status: str  # "Pending Deposit", "Deposited", "Cleared", "Bounced"
    notes: Optional[str] = None

class ChequeResponse(ChequeBase):
    id: int
    business_id: int
    customer_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
