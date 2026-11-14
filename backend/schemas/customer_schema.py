from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    name: str
    company_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    city: Optional[str] = "Lahore"
    address: Optional[str] = None
    ntn_number: Optional[str] = None
    credit_limit: Optional[float] = 100000.0
    payment_terms_days: Optional[int] = 15

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    ntn_number: Optional[str] = None
    credit_limit: Optional[float] = None
    payment_terms_days: Optional[int] = None
    is_active: Optional[bool] = None

class CustomerResponse(CustomerBase):
    id: int
    business_id: int
    current_balance: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
