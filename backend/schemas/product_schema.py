from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    sku: str
    name: str
    category: Optional[str] = "General"
    unit: Optional[str] = "Carton"
    stock_quantity: Optional[float] = 0.0
    unit_cost: Optional[float] = 0.0
    unit_price: Optional[float] = 0.0
    reorder_level: Optional[float] = 10.0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    stock_quantity: Optional[float] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    reorder_level: Optional[float] = None

class ProductResponse(ProductBase):
    id: int
    business_id: int
    created_at: datetime

    class Config:
        from_attributes = True
