from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import Invoice, Payment, User
from ..schemas.reconciliation_schema import ManualReconciliationRequest, AutoFIFOReconcileRequest, ReconciliationResult
from ..dependencies import get_current_user
from ..services.reconciliation_service import ReconciliationService
from ..services.report_service import ReportService

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation Engine"])

@router.post("/auto-fifo", response_model=ReconciliationResult)
def run_auto_fifo(
    req: AutoFIFOReconcileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = ReconciliationService.auto_reconcile_fifo(
        db=db,
        business_id=current_user.business_id,
        customer_id=req.customer_id,
        user_id=current_user.id
    )
    return result

@router.post("/manual", response_model=ReconciliationResult)
def run_manual_reconcile(
    req: ManualReconciliationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allocs = [
        {"invoice_id": item.invoice_id, "amount_to_allocate": item.amount_to_allocate}
        for item in req.allocations
    ]
    result = ReconciliationService.manual_reconcile(
        db=db,
        business_id=current_user.business_id,
        payment_id=req.payment_id,
        allocations=allocs,
        user_id=current_user.id
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@router.get("/open-items")
def get_reconciliation_open_items(
    customer_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve open invoices and unallocated payments for the reconciliation workspace."""
    p_query = db.query(Payment).filter(
        Payment.business_id == current_user.business_id,
        Payment.unallocated_amount > 0
    )
    i_query = db.query(Invoice).filter(
        Invoice.business_id == current_user.business_id,
        Invoice.status.in_(["Issued", "Partially Paid", "Overdue"]),
        Invoice.balance_due > 0
    )

    if customer_id:
        p_query = p_query.filter(Payment.customer_id == customer_id)
        i_query = i_query.filter(Invoice.customer_id == customer_id)

    unallocated_payments = [
        {
            "id": p.id,
            "payment_number": p.payment_number,
            "customer_id": p.customer_id,
            "customer_name": p.customer.name if p.customer else "",
            "payment_date": p.payment_date.isoformat(),
            "total_amount": p.amount,
            "unallocated_amount": p.unallocated_amount,
            "payment_method": p.payment_method,
            "reference_number": p.reference_number
        }
        for p in p_query.order_by(Payment.payment_date.asc()).all()
    ]

    open_invoices = [
        {
            "id": i.id,
            "invoice_number": i.invoice_number,
            "customer_id": i.customer_id,
            "customer_name": i.customer.name if i.customer else "",
            "issue_date": i.issue_date.isoformat(),
            "due_date": i.due_date.isoformat(),
            "total_amount": i.total_amount,
            "paid_amount": i.paid_amount,
            "balance_due": i.balance_due,
            "status": i.status
        }
        for i in i_query.order_by(Invoice.issue_date.asc()).all()
    ]

    return {
        "unallocated_payments": unallocated_payments,
        "open_invoices": open_invoices
    }

@router.get("/summary")
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ReportService.get_reconciliation_summary(db, current_user.business_id)
