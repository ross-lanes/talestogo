"""
Authentication Router
Handles user registration, login (email/password, Microsoft Entra ID OAuth), and profile management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..auth import (
    get_current_user,
    authenticate_user,
    create_access_token,
    get_password_hash,
    encrypt_api_key,
    verify_microsoft_token,
    get_or_create_oauth_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=schemas.User, status_code=201)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (invite-only).
    User account will be inactive until admin approves.
    """
    # Check if user already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    new_user = crud.create_user(db=db, user=user, hashed_password=hashed_password, is_invited=False)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns JWT access token.
    """
    user = authenticate_user(db, email=user_credentials.email, password=user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active. Please contact admin for approval."
        )

    # Update last_login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/microsoft", response_model=schemas.Token)
def microsoft_login(microsoft_token: schemas.MicrosoftLogin, db: Session = Depends(get_db)):
    """
    Login with Microsoft OAuth.
    Accepts Microsoft ID token and returns JWT access token.
    Creates new user if doesn't exist (auto-activated for admin).
    """
    # Verify Microsoft token and get user info
    microsoft_info = verify_microsoft_token(microsoft_token.token)

    # Ensure email is verified
    if not microsoft_info.get('email_verified'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified with Microsoft"
        )

    # Get or create user
    user = get_or_create_oauth_user(db, microsoft_info, provider='microsoft')

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active. Please contact admin for approval."
        )

    # Update last_login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/dev-login", response_model=schemas.Token)
def dev_login(db: Session = Depends(get_db)):
    """
    Development-only login endpoint.
    Automatically logs in as the first admin user (or creates one).
    WARNING: Only enable this in development environments!
    """
    import os
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login is disabled in production"
        )

    # Find or create dev admin user
    dev_email = "rkremen@pppl.gov"
    user = db.query(models.User).filter(models.User.email == dev_email).first()

    if not user:
        # Create dev admin user
        from ..auth import get_tenant_id_for_email
        tenant_id = get_tenant_id_for_email(db, dev_email)
        user = models.User(
            email=dev_email,
            full_name="Rachel Kremen (Dev)",
            tenant_id=tenant_id,
            allowed_products=["tales", "heads", "canon"],
            is_active=True,
            is_admin=True,
            is_invited=True,
            hashed_password=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Get current logged-in user information."""
    return current_user


@router.put("/me", response_model=schemas.User)
def update_current_user_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile and API keys."""
    updated_user = crud.update_user(
        db,
        user_id=current_user.id,
        user_update=user_update,
        encrypt_keys_func=encrypt_api_key
    )
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user
