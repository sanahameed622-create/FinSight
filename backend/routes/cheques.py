from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ..database import get_db
from ..models import PostDatedCheque, Customer, Payment, User, ActivityLog
from ..schemas.cheque_schema import ChequeCreate, ChequeStatusUpdate, ChequeResponse
from ..dependencies import get_current_user
from ..services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/cheques", tags=["Post-Dated Cheques (PDC)"])

@router.get("", response_model=List[ChequeResponse])
def get_cheques(
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PostDatedCheque).filter(PostDatedCheque.business_id == current_user.business_id)

    if customer_id:
        query = query.filter(PostDatedCheque.customer_id == customer_id)
    if status and status != "All":
        query = query.filter(PostDatedCheque.status == status)

    cheques = query.order_by(PostDatedCheque.maturity_date.asc()).all()

    results = []
    for c in cheques:
        res = ChequeResponse.from_orm(c)
        res.customer_name = c.customer.name if c.customer else "Unknown"
        results.append(res)
    return results

@router.post("", response_model=ChequeResponse, status_code=status.HTTP_201_CREATED)
def record_cheque(
    chq_in: ChequeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == chq_in.customer_id,
        Customer.business_id == current_user.business_id
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    new_cheque = PostDatedCheque(
        business_id=current_user.business_id,
        customer_id=customer.id,
        cheque_number=chq_in.cheque_number,
        bank_name=chq_in.bank_name,
        amount=round(chq_in.amount, 2),
        issue_date=chq_in.issue_date,
        maturity_date=chq_in.maturity_date,
        status="Pending Deposit",
        notes=chq_in.notes
    )
    db.add(new_cheque)
    db.flush()

    log = ActivityLog(
        business_id=current_user.business_id,
        user_id=current_user.id,
        action_type="RECORD_PDC",
        description=f"Received Post-Dated Cheque #{new_cheque.cheque_number} ({new_cheque.bank_name}) for {customer.name} (Amount: {new_cheque.amount:,.2f}, Maturity: {new_cheque.maturity_date})"
    )
    db.add(log)
    db.commit()
    db.refresh(new_cheque)

    res = ChequeResponse.from_orm(new_cheque)
    res.customer_name = customer.name
    return res

@router.put("/{cheque_id}/status", response_model=ChequeResponse)
def update_cheque_status(
    cheque_id: int,
    status_update: ChequeStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cheque = db.query(PostDatedCheque).filter(
        PostDatedCheque.id == cheque_id,
        PostDatedCheque.business_id == current_user.business_id
    ).first()

    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")

    old_status = cheque.status
    new_status = status_update.status
    cheque.status = new_status
    if status_update.notes:
        cheque.notes = status_update.notes

    # If status becomes "Cleared", automatically record as cleared Payment and auto-reconcile FIFO!
    if new_status == "Cleared" and old_status != "Cleared":
        pay_count = db.query(Payment).filter(Payment.business_id == current_user.business_id).count()
        pay_num = f"PAY-CHQ-{date.today().year}-{pay_count + 1:04d}"

        cleared_payment = Payment(
            business_id=current_user.business_id,
            customer_id=cheque.customer_id,
            payment_number=pay_num,
            payment_date=date.today(),
            amount=cheque.amount,
            unallocated_amount=cheque.amount,
            payment_method="Cheque",
            reference_number=f"Cheque #{cheque.cheque_number}",
            bank_name=cheque.bank_name,
            status="Unallocated",
            notes=f"Cleared Post-Dated Cheque #{cheque.cheque_number}"
        )
        db.add(cleared_payment)
        db.flush()

        # Run Auto FIFO reconciliation for this cleared payment
        ReconciliationService.auto_reconcile_fifo(
            db=db,
            business_id=current_user.business_id,
            customer_id=cheque.customer_id,
            user_id=current_user.id
        )

    log = ActivityLog(
        business_id=current_user.business_id,
        user_id=current_user.id,
        action_type="CHEQUE_STATUS_UPDATE",
        description=f"Post-Dated Cheque #{cheque.cheque_number} status updated to '{new_status}'."
    )
    db.add(log)
    db.commit()
    db.refresh(cheque)

    res = ChequeResponse.from_orm(cheque)
    res.customer_name = cheque.customer.name if cheque.customer else "Unknown"
    return res
