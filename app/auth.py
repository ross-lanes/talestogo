"""
Authentication utilities for TALES multi-user system.
Handles JWT tokens, password hashing, and user verification.
Supports both traditional email/password and Google OAuth authentication.
"""

from dotenv import load_dotenv
load_dotenv(override=True)  # Load environment variables FIRST, override existing ones

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db
from cryptography.fernet import Fernet
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Admin Configuration
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "robotrachel@gmail.com")

# Encryption key for API keys (must be stored securely in production)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

# HTTP Bearer token security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for secure storage."""
    if not api_key:
        return None
    return cipher_suite.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key for use."""
    if not encrypted_key:
        return None
    return cipher_suite.decrypt(encrypted_key.encode()).decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_invitation_token(email: str, full_name: str, expires_days: int = 7) -> tuple[str, datetime]:
    """Create a JWT invitation token that expires in N days."""
    expire = datetime.utcnow() + timedelta(days=expires_days)
    to_encode = {
        "email": email,
        "full_name": full_name,
        "exp": expire,
        "type": "invitation"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire


def verify_invitation_token(token: str) -> dict:
    """Verify and decode an invitation token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "invitation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invitation token"
            )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token"
        )


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Get the current authenticated user from JWT token.
    This dependency should be used on all protected routes.
    """
    token = credentials.credentials
    payload = verify_token(token)

    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active. Please contact admin for approval.",
        )

    return user


def get_current_admin_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Verify that the current user is an admin.
    Use this dependency for admin-only routes.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action",
        )
    return current_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Authenticate a user by email and password."""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not user.hashed_password:
        # OAuth user trying to login with password
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def verify_google_token(token: str) -> dict:
    """
    Verify Google OAuth ID token and return user info.
    Returns dict with: email, name, picture, sub (google_id)
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Verify issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        return {
            'email': idinfo['email'],
            'name': idinfo.get('name'),
            'picture': idinfo.get('picture'),
            'google_id': idinfo['sub'],
            'email_verified': idinfo.get('email_verified', False)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )


def get_or_create_oauth_user(db: Session, google_info: dict) -> models.User:
    """
    Get existing OAuth user or create a new one.
    New OAuth users are automatically activated.
    """
    # Check if user exists by google_id
    user = db.query(models.User).filter(models.User.google_id == google_info['google_id']).first()

    if user:
        # Update user info if needed
        if user.picture_url != google_info.get('picture'):
            user.picture_url = google_info.get('picture')
        if user.full_name != google_info.get('name'):
            user.full_name = google_info.get('name')
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    # Check if user exists by email (maybe they registered with password before)
    user = db.query(models.User).filter(models.User.email == google_info['email']).first()

    if user:
        # Link Google account to existing user
        user.google_id = google_info['google_id']
        user.oauth_provider = 'google'
        user.picture_url = google_info.get('picture')
        if not user.full_name:
            user.full_name = google_info.get('name')
        # Only auto-activate if they're the admin, otherwise keep existing status
        if google_info['email'].lower() == ADMIN_EMAIL.lower():
            user.is_active = True
            user.is_admin = True
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    # Create new user
    # Check if this email is the admin email
    is_admin_user = (google_info['email'].lower() == ADMIN_EMAIL.lower())

    new_user = models.User(
        email=google_info['email'],
        google_id=google_info['google_id'],
        oauth_provider='google',
        full_name=google_info.get('name'),
        picture_url=google_info.get('picture'),
        is_active=is_admin_user,  # Only auto-activate admin user, others need approval
        is_admin=is_admin_user,  # Make admin if email matches ADMIN_EMAIL
        is_invited=False,  # Require admin approval for all new users
        hashed_password=None  # No password for OAuth users
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
