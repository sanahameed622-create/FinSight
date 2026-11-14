from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Product, User, ActivityLog
from ..schemas.product_schema import ProductCreate, ProductUpdate, ProductResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/products", tags=["Inventory & Products"])

@router.get("", response_model=List[ProductResponse])
def get_products(
    search: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.business_id == current_user.business_id)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_filter)) |
            (Product.sku.ilike(search_filter)) |
            (Product.category.ilike(search_filter))
        )

    if low_stock_only:
        query = query.filter(Product.stock_quantity <= Product.reorder_level)

    return query.order_by(Product.name.asc()).all()

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    prod_in: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check SKU uniqueness in business
    existing = db.query(Product).filter(
        Product.business_id == current_user.business_id,
        Product.sku == prod_in.sku
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Product with SKU '{prod_in.sku}' already exists.")

    new_prod = Product(
        business_id=current_user.business_id,
        sku=prod_in.sku,
        name=prod_in.name,
        category=prod_in.category or "General",
        unit=prod_in.unit or "Carton",
        stock_quantity=prod_in.stock_quantity or 0.0,
        unit_cost=prod_in.unit_cost or 0.0,
        unit_price=prod_in.unit_price or 0.0,
        reorder_level=prod_in.reorder_level or 10.0
    )
    db.add(new_prod)
    db.flush()

    log = ActivityLog(
        business_id=current_user.business_id,
        user_id=current_user.id,
        action_type="CREATE_PRODUCT",
        description=f"Added product '{new_prod.name}' (SKU: {new_prod.sku}) with stock {new_prod.stock_quantity} {new_prod.unit}s."
    )
    db.add(log)
    db.commit()
    db.refresh(new_prod)
    return new_prod

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    prod_in: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prod = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id
    ).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = prod_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prod, field, value)

    db.commit()
    db.refresh(prod)
    return prod

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prod = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id
    ).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(prod)
    db.commit()
    return {"success": True, "message": f"Product '{prod.name}' has been deleted."}
