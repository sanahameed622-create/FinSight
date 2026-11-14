from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ..database import get_db
from ..models import Payment, Customer, User, ActivityLog
from ..schemas.payment_schema import PaymentCreate, PaymentResponse, AllocationItem
from ..dependencies import get_current_user
from ..services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/payments", tags=["Payments"])

def generate_payment_number(db: Session, business_id: int) -> str:
    count = db.query(Payment).filter(Payment.business_id == business_id).count()
    candidate = f"PAY-{business_id:03d}-{date.today().year}-{count + 1:04d}"
    while db.query(Payment).filter(Payment.payment_number == candidate).first():
        count += 1
        candidate = f"PAY-{business_id:03d}-{date.today().year}-{count + 1:04d}"
    return candidate

@router.get("", response_model=List[PaymentResponse])
def get_payments(
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Payment).filter(Payment.business_id == current_user.business_id)

    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)
    if status and status != "All":
        query = query.filter(Payment.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.join(Customer).filter(
            (Payment.payment_number.ilike(search_filter)) |
            (Payment.reference_number.ilike(search_filter)) |
            (Customer.name.ilike(search_filter))
        )

    payments = query.order_by(Payment.payment_date.desc(), Payment.id.desc()).all()

    results = []
    for p in payments:
        res = PaymentResponse.from_orm(p)
        res.customer_name = p.customer.name if p.customer else "Unknown"
        res.allocations = [
            AllocationItem(
                id=a.id,
                invoice_id=a.invoice_id,
                invoice_number=a.invoice.invoice_number if a.invoice else "INV",
                allocated_amount=a.allocated_amount,
                allocated_at=a.allocated_at,
                notes=a.notes
            )
            for a in p.allocations
        ]
        results.append(res)
    return results

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    pay_in: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == pay_in.customer_id,
        Customer.business_id == current_user.business_id
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if pay_in.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero.")

    pay_num = pay_in.payment_number or generate_payment_number(db, current_user.business_id)

    new_payment = Payment(
        business_id=current_user.business_id,
        customer_id=customer.id,
        payment_number=pay_num,
        payment_date=pay_in.payment_date,
        amount=round(pay_in.amount, 2),
        unallocated_amount=round(pay_in.amount, 2),
        payment_method=pay_in.payment_method,
        reference_number=pay_in.reference_number,
        bank_name=pay_in.bank_name,
        status="Unallocated",
        notes=pay_in.notes
    )
    db.add(new_payment)
    db.flush()

    # Recalculate customer balance
    ReconciliationService.recalculate_customer_balance(db, customer.id)

    log = ActivityLog(
        business_id=current_user.business_id,
        user_id=current_user.id,
        action_type="RECORD_PAYMENT",
        description=f"Recorded payment {new_payment.payment_number} from {customer.name} (PKR {new_payment.amount:,.2f}) via {new_payment.payment_method}"
    )
    db.add(log)
    db.commit()
    db.refresh(new_payment)

    # Optional Auto FIFO Reconciliation upon recording
    if pay_in.auto_allocate_fifo:
        ReconciliationService.auto_reconcile_fifo(
            db=db,
            business_id=current_user.business_id,
            customer_id=customer.id,
            user_id=current_user.id
        )
        db.refresh(new_payment)

    res = PaymentResponse.from_orm(new_payment)
    res.customer_name = customer.name
    res.allocations = [
        AllocationItem(
            id=a.id,
            invoice_id=a.invoice_id,
            invoice_number=a.invoice.invoice_number if a.invoice else "INV",
            allocated_amount=a.allocated_amount,
            allocated_at=a.allocated_at,
            notes=a.notes
        )
        for a in new_payment.allocations
    ]
    return res

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.business_id == current_user.business_id
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")

    res = PaymentResponse.from_orm(p)
    res.customer_name = p.customer.name if p.customer else "Unknown"
    res.allocations = [
        AllocationItem(
            id=a.id,
            invoice_id=a.invoice_id,
            invoice_number=a.invoice.invoice_number if a.invoice else "INV",
            allocated_amount=a.allocated_amount,
            allocated_at=a.allocated_at,
            notes=a.notes
        )
        for a in p.allocations
    ]
    return res
