from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    role: Optional[str] = "admin"

class UserRegister(UserBase):
    password: str
    business_name: str
    city: Optional[str] = "Lahore"
    registration_no: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    business_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    business_name: Optional[str] = None
    currency: str = "PKR"
