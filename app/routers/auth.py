"""
Authentication Router
Handles user registration, login (email/password, Google, Microsoft OAuth), and profile management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address

from .. import crud, models, schemas
from ..database import get_db
from ..auth import (
    get_current_user,
    authenticate_user,
    create_access_token,
    get_password_hash,
    encrypt_api_key,
    verify_google_token,
    verify_microsoft_token,
    get_or_create_oauth_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..utils.password_validation import validate_password_strength, format_password_errors

# Get limiter from app state
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=schemas.User, status_code=201)
@limiter.limit("5/minute")  # Strict limit for registration
async def register_user(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (invite-only).
    User account will be inactive until admin approves.
    Rate limited to 5 attempts per minute to prevent abuse.

    Password requirements:
    - At least 8 characters long
    - Contains uppercase, lowercase, number, and special character
    """
    # Check if user already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength
    is_valid, password_errors = validate_password_strength(user.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=format_password_errors(password_errors)
        )

    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    new_user = crud.create_user(db=db, user=user, hashed_password=hashed_password, is_invited=False)
    return new_user


@router.post("/login", response_model=schemas.Token)
@limiter.limit("10/minute")  # Limit login attempts to prevent brute force
async def login(request: Request, user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns JWT access token.
    Rate limited to 10 attempts per minute to prevent brute force attacks.
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

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/google", response_model=schemas.Token)
@limiter.limit("10/minute")  # Limit OAuth login attempts
async def google_login(request: Request, google_token: schemas.GoogleLogin, db: Session = Depends(get_db)):
    """
    Login with Google OAuth.
    Accepts Google ID token and returns JWT access token.
    Creates new user if doesn't exist (auto-activated).
    Rate limited to 10 attempts per minute.
    """
    # Verify Google token and get user info
    google_info = verify_google_token(google_token.token)

    # Ensure email is verified
    if not google_info.get('email_verified'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified with Google"
        )

    # Get or create user
    user = get_or_create_oauth_user(db, google_info)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active. Please contact admin for approval."
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/microsoft", response_model=schemas.Token)
@limiter.limit("10/minute")  # Limit OAuth login attempts
async def microsoft_login(request: Request, microsoft_token: schemas.MicrosoftLogin, db: Session = Depends(get_db)):
    """
    Login with Microsoft OAuth.
    Accepts Microsoft ID token and returns JWT access token.
    Creates new user if doesn't exist (auto-activated for admin).
    Rate limited to 10 attempts per minute.
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

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Get current logged-in user information with allowed products."""
    # Get user's allowed products using the helper function
    allowed_products = crud.get_user_allowed_products(current_user)

    # Create a dict from the user model and add allowed_products as a list
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "organization": current_user.organization,
        "is_admin": current_user.is_admin,
        "is_active": current_user.is_active,
        "is_invited": current_user.is_invited,
        "google_id": current_user.google_id,
        "oauth_provider": current_user.oauth_provider,
        "picture_url": current_user.picture_url,
        "invitation_expires_at": current_user.invitation_expires_at,
        "tenant_id": current_user.tenant_id,
        "allowed_products": allowed_products,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }
    return user_dict


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
