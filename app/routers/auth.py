from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserProfileResponse,
    UserUpdateProfileRequest,
    AuthTokenResponse,
)
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Use Case 1: User Registration (Table 4.1 in F26-201).
    Registers farmer with phone number, full name, district, pin/password, role, and language.
    """
    existing_user = db.query(User).filter(User.phone_number == req.phone_number).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered. Please sign in instead."
        )

    password_hash = get_password_hash(req.password)
    user_id = f"usr_{uuid.uuid4().hex[:12]}"

    new_user = User(
        user_id=user_id,
        full_name=req.full_name,
        phone_number=req.phone_number,
        password_hash=password_hash,
        role=req.role,
        district=req.district,
        language_pref=req.language_pref,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(subject=new_user.user_id)
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse.model_validate(new_user)
    )

@router.post("/login", response_model=AuthTokenResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Use Case 2: User Login (Table 4.2 in F26-201).
    Authenticates farmer by mobile number and PIN/password.
    Generic error returned on either invalid phone or invalid PIN to prevent user enumeration.
    """
    user = db.query(User).filter(User.phone_number == req.phone_number).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect mobile number or PIN entered. Please verify your credentials and try again."
        )

    token = create_access_token(subject=user.user_id)
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse.model_validate(user)
    )

@router.get("/me", response_model=UserProfileResponse)
def get_authenticated_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile of currently authenticated farmer."""
    return UserProfileResponse.model_validate(current_user)

@router.put("/me", response_model=UserProfileResponse)
def update_profile(
    req: UserUpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile details (name, district, language preference)."""
    if req.full_name is not None:
        current_user.full_name = req.full_name
    if req.district is not None:
        current_user.district = req.district
    if req.language_pref is not None:
        current_user.language_pref = req.language_pref

    db.commit()
    db.refresh(current_user)
    return UserProfileResponse.model_validate(current_user)
