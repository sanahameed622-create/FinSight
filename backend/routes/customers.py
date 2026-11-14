from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Customer, User, ActivityLog
from ..schemas.customer_schema import CustomerCreate, CustomerUpdate, CustomerResponse
from ..dependencies import get_current_user
from ..services.report_service import ReportService

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("", response_model=List[CustomerResponse])
def get_customers(
    search: Optional[str] = Query(None, description="Search by name, company, or phone"),
    city: Optional[str] = Query(None, description="Filter by city"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Customer).filter(
        Customer.business_id == current_user.business_id,
        Customer.is_active == True
    )
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Customer.name.ilike(search_filter)) |
            (Customer.company_name.ilike(search_filter)) |
            (Customer.phone.ilike(search_filter))
        )
    if city:
        query = query.filter(Customer.city == city)

    return query.order_by(Customer.name.asc()).all()

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_customer = Customer(
        business_id=current_user.business_id,
        name=customer_in.name,
        company_name=customer_in.company_name or customer_in.name,
        phone=customer_in.phone,
        email=customer_in.email,
        city=customer_in.city or "Lahore",
        address=customer_in.address,
        ntn_number=customer_in.ntn_number,
        credit_limit=customer_in.credit_limit or 100000.0,
        payment_terms_days=customer_in.payment_terms_days or 15,
        current_balance=0.0
    )
    db.add(new_customer)
    db.flush()

    log = ActivityLog(
        business_id=current_user.business_id,
        user_id=current_user.id,
        action_type="CREATE_CUSTOMER",
        description=f"Created customer '{new_customer.name}' with credit limit PKR {new_customer.credit_limit:,.2f}"
    )
    db.add(log)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.business_id == current_user.business_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.business_id == current_user.business_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.business_id == current_user.business_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Soft delete
    customer.is_active = False
    db.commit()
    return {"success": True, "message": f"Customer '{customer.name}' has been deactivated."}

@router.get("/{customer_id}/ledger")
def get_customer_ledger(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ReportService.get_customer_ledger(db, current_user.business_id, customer_id)
