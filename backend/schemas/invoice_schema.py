from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class InvoiceItemBase(BaseModel):
    item_description: str
    quantity: float = 1.0
    unit_price: float
    total: Optional[float] = None

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItemResponse(InvoiceItemBase):
    id: int
    invoice_id: int

    class Config:
        from_attributes = True

class InvoiceCreate(BaseModel):
    customer_id: int
    invoice_number: Optional[str] = None  # Auto-generated if not provided
    issue_date: date
    due_date: date
    tax_amount: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    notes: Optional[str] = None
    items: List[InvoiceItemCreate]

class InvoiceResponse(BaseModel):
    id: int
    business_id: int
    customer_id: int
    customer_name: Optional[str] = None
    invoice_number: str
    issue_date: date
    due_date: date
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    paid_amount: float
    balance_due: float
    status: str
    notes: Optional[str] = None
    created_at: datetime
    items: List[InvoiceItemResponse] = []

    class Config:
        from_attributes = True
