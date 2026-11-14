from pydantic import BaseModel
from typing import List, Optional

class ManualAllocationItem(BaseModel):
    invoice_id: int
    amount_to_allocate: float

class ManualReconciliationRequest(BaseModel):
    payment_id: int
    allocations: List[ManualAllocationItem]

class AutoFIFOReconcileRequest(BaseModel):
    customer_id: Optional[int] = None  # Reconcile specific customer or all

class ReconciliationResult(BaseModel):
    success: bool
    message: str
    reconciled_allocations_count: int
    total_amount_allocated: float
    unallocated_remaining: float
