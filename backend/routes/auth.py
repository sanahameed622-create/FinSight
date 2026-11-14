from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Business, ActivityLog
from ..schemas.user_schema import UserRegister, UserLogin, TokenResponse, UserResponse
from ..utils.security import get_password_hash, verify_password, create_access_token
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    # Create Business
    business = Business(
        name=user_in.business_name,
        city=user_in.city or "Lahore",
        registration_no=user_in.registration_no,
        currency="PKR"
    )
    db.add(business)
    db.flush()

    # Create User
    new_user = User(
        business_id=business.id,
        full_name=user_in.full_name,
        email=user_in.email,
        phone=user_in.phone,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role or "admin"
    )
    db.add(new_user)
    db.flush()

    # Activity log
    log = ActivityLog(
        business_id=business.id,
        user_id=new_user.id,
        action_type="USER_REGISTER",
        description=f"User {new_user.full_name} registered business {business.name}."
    )
    db.add(log)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user,
        "business_name": business.name,
        "currency": business.currency
    }

@router.post("/login", response_model=TokenResponse)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated."
        )

    business_name = user.business.name if user.business else "FinSight Workspace"
    currency = user.business.currency if user.business else "PKR"
    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "business_name": business_name,
        "currency": currency
    }

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
