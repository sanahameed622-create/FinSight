from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ..database import get_db
from ..models import Invoice, InvoiceItem, Customer, User, ActivityLog, Product
from ..schemas.invoice_schema import InvoiceCreate, InvoiceResponse
from ..dependencies import get_current_user
from ..services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/invoices", tags=["Invoices"])

def generate_invoice_number(db: Session, business_id: int) -> str:
    count = db.query(Invoice).filter(Invoice.business_id == business_id).count()
    candidate = f"INV-{business_id:03d}-{date.today().year}-{count + 1:04d}"
    while db.query(Invoice).filter(Invoice.invoice_number == candidate).first():
        count += 1
        candidate = f"INV-{business_id:03d}-{date.today().year}-{count + 1:04d}"
    return candidate

@router.get("", response_model=List[InvoiceResponse])
def get_invoices(
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Invoice).filter(Invoice.business_id == current_user.business_id)

    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    if status and status != "All":
        query = query.filter(Invoice.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.join(Customer).filter(
            (Invoice.invoice_number.ilike(search_filter)) |
            (Customer.name.ilike(search_filter))
        )

    invoices = query.order_by(Invoice.issue_date.desc(), Invoice.id.desc()).all()

    # Format response with customer name
    results = []
    for inv in invoices:
        res = InvoiceResponse.from_orm(inv)
        res.customer_name = inv.customer.name if inv.customer else "Unknown"
        results.append(res)
    return results

@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    inv_in: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == inv_in.customer_id,
        Customer.business_id == current_user.business_id
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    invoice_number = inv_in.invoice_number or generate_invoice_number(db, current_user.business_id)

    # Check uniqueness
    existing = db.query(Invoice).filter(
        Invoice.business_id == current_user.business_id,
        Invoice.invoice_number == invoice_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Invoice number '{invoice_number}' already exists.")

    # Calculate item totals
    subtotal = 0.0
    items_to_add = []
    for item in inv_in.items:
        line_total = round(item.quantity * item.unit_price, 2)
        subtotal += line_total
        items_to_add.append(InvoiceItem(
            item_description=item.item_description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=line_total
        ))

    tax = inv_in.tax_amount or 0.0
    discount = inv_in.discount_amount or 0.0
    total_amount = round(max(0.0, subtotal + tax - discount), 2)

    new_invoice = Invoice(
        business_id=current_user.business_id,
        customer_id=customer.id,
        invoice_number=invoice_number,
        issue_date=inv_in.issue_date,
        due_date=inv_in.due_date,
        subtotal=round(subtotal, 2),
        tax_amount=tax,
        discount_amount=discount,
        total_amount=total_amount,
        paid_amount=0.0,
        balance_due=total_amount,
        status="Issued" if total_amount > 0 else "Paid",
        notes=inv_in.notes
    )
    db.add(new_invoice)
    db.flush()

    for itm in items_to_add:
        itm.invoice_id = new_invoice.id
        db.add(itm)

        # Inventory Auto-Deduction
        prod = db.query(Product).filter(
            Product.business_id == current_user.business_id,
            Product.name == itm.item_description
        ).first()
        if prod:
            prod.stock_quantity = max(0.0, prod.stock_quantity - itm.quantity)

    # Recalculate customer balance
    ReconciliationService.recalculate_customer_balance(db, customer.id)

    # Log Activity
    log = ActivityLog(
        business_id=current_user.business_id,
        user_id=current_user.id,
        action_type="CREATE_INVOICE",
        description=f"Created invoice {new_invoice.invoice_number} for {customer.name} (PKR {total_amount:,.2f})"
    )
    db.add(log)
    db.commit()
    db.refresh(new_invoice)

    res = InvoiceResponse.from_orm(new_invoice)
    res.customer_name = customer.name
    return res

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.business_id == current_user.business_id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    res = InvoiceResponse.from_orm(inv)
    res.customer_name = inv.customer.name if inv.customer else "Unknown"
    return res

@router.delete("/{invoice_id}")
def cancel_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.business_id == current_user.business_id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if inv.paid_amount > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel an invoice with allocated payments. Reconcile or unallocate payments first."
        )

    inv.status = "Cancelled"
    ReconciliationService.recalculate_customer_balance(db, inv.customer_id)

    log = ActivityLog(
        business_id=current_user.business_id,
        user_id=current_user.id,
        action_type="CANCEL_INVOICE",
        description=f"Cancelled invoice {inv.invoice_number}."
    )
    db.add(log)
    db.commit()

    return {"success": True, "message": f"Invoice {inv.invoice_number} has been cancelled."}
