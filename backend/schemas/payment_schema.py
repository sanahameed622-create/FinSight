from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class AllocationItem(BaseModel):
    id: int
    invoice_id: int
    invoice_number: Optional[str] = None
    allocated_amount: float
    allocated_at: datetime
    notes: Optional[str] = None

class PaymentCreate(BaseModel):
    customer_id: int
    payment_number: Optional[str] = None  # Auto-generated if omitted
    payment_date: date
    amount: float
    payment_method: str = "Bank Transfer"
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    auto_allocate_fifo: bool = True  # Automatically apply FIFO reconciliation to oldest unpaid invoices

class PaymentResponse(BaseModel):
    id: int
    business_id: int
    customer_id: int
    customer_name: Optional[str] = None
    payment_number: str
    payment_date: date
    amount: float
    unallocated_amount: float
    payment_method: str
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    allocations: List[AllocationItem] = []

    class Config:
        from_attributes = True
