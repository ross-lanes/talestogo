from dotenv import load_dotenv
load_dotenv(override=True)  # Load environment variables from .env file

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from datetime import timedelta
import os
import subprocess
import io
import base64
from pathlib import Path

# Use explicit imports from the 'app' package
from app import crud, models, schemas
from app.database import SessionLocal, engine
from app.routers import analytics
from app.auth import (
    get_current_user,
    get_current_admin_user,
    authenticate_user,
    create_access_token,
    get_password_hash,
    encrypt_api_key,
    decrypt_api_key,
    verify_google_token,
    verify_microsoft_token,
    get_or_create_oauth_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# This line ensures tables are created if they don't exist when the app starts.
# It's convenient for development. For production, you'd use a migration tool.
models.Base.metadata.create_all(bind=engine)

# Create the FastAPI app instance
app = FastAPI(
    title="Tales",
    description="An AI tool for tracking and analyzing LLM brand depictions.",
    version="0.1.0"
)

# Configure CORS to allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "https://tales-frontend.onrender.com",  # Production frontend (legacy)
        "https://tales.robotrachel.com"  # Production frontend (custom domain)
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(analytics.router)

# --- Dependencies ---
def get_db():
    """
    Dependency function that provides a database session per request.
    Ensures the session is always closed, even if errors occur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_active_brand_id(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Optional[int]:
    """
    Helper function to get the active brand_id for the current user.
    Returns None if no active brand exists (allows multi-brand view).
    """
    active_brand = crud.get_active_brand(db, user_id=current_user.id)
    return active_brand.id if active_brand else None

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint to check if the API is running."""
    return {"message": "Welcome to the TALES API!"}


# --- Authentication Endpoints ---
@app.post("/auth/register", response_model=schemas.User, status_code=201, tags=["Authentication"])
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


@app.post("/auth/login", response_model=schemas.Token, tags=["Authentication"])
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

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/google", response_model=schemas.Token, tags=["Authentication"])
def google_login(google_token: schemas.GoogleLogin, db: Session = Depends(get_db)):
    """
    Login with Google OAuth.
    Accepts Google ID token and returns JWT access token.
    Creates new user if doesn't exist (auto-activated).
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


@app.post("/auth/microsoft", response_model=schemas.Token, tags=["Authentication"])
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

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.User, tags=["Authentication"])
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Get current logged-in user information."""
    return current_user


@app.put("/auth/me", response_model=schemas.User, tags=["Authentication"])
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


# --- Admin User Management Endpoints ---
@app.get("/admin/users", response_model=List[schemas.User], tags=["Admin"])
def list_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    return crud.get_users(db, skip=skip, limit=limit)


@app.post("/admin/users/invite", response_model=schemas.User, status_code=201, tags=["Admin"])
def invite_user(
    user_invite: schemas.UserInvite,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create an invited user (admin only).
    Invited users are pre-approved (is_active=True).
    """
    # Check if user already exists
    db_user = crud.get_user_by_email(db, email=user_invite.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create temporary password (user should change on first login)
    temp_password = "TempPassword123!"
    hashed_password = get_password_hash(temp_password)

    # Create user object
    user_create = schemas.UserCreate(
        email=user_invite.email,
        password=temp_password,
        full_name=user_invite.full_name,
        organization=user_invite.organization
    )

    new_user = crud.create_user(db=db, user=user_create, hashed_password=hashed_password, is_invited=True)

    # Activate invited user immediately
    admin_update = schemas.UserAdminUpdate(is_active=True)
    crud.admin_update_user(db, user_id=new_user.id, user_update=admin_update)

    return new_user


@app.put("/admin/users/{user_id}", response_model=schemas.User, tags=["Admin"])
def admin_update_user_status(
    user_id: int,
    user_update: schemas.UserAdminUpdate,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user status (activate/deactivate, make admin) - admin only."""
    updated_user = crud.admin_update_user(db, user_id=user_id, user_update=user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@app.delete("/admin/users/{user_id}", response_model=schemas.User, tags=["Admin"])
def admin_delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only). Cannot delete yourself."""
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )

    # Get the user
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete the user (will cascade delete all related data)
    db.delete(user_to_delete)
    db.commit()

    return user_to_delete


# --- Invitation Endpoints ---
@app.post("/admin/users/create-invite", response_model=schemas.InvitationResponse, status_code=201, tags=["Admin", "Invitations"])
def create_invitation(
    invitation: schemas.InvitationCreate,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Add user email to approved list (admin only).
    User can then login directly with Google OAuth.
    No invitation token needed - just tell them to visit the site and sign in with Google.
    """
    # Check if user already exists
    existing_user = crud.get_user_by_email(db, email=invitation.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create pre-approved user (active and ready for OAuth login)
    new_user = models.User(
        email=invitation.email,
        full_name=invitation.full_name,
        is_invited=True,
        is_active=True,  # Pre-approved, will be activated on first Google login
        invitation_token=None,
        invitation_expires_at=None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return simple login URL
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    return schemas.InvitationResponse(
        email=invitation.email,
        full_name=invitation.full_name,
        invitation_token="",  # No token needed
        expires_at=None,
        invitation_url=frontend_url  # Just send them to the main site
    )


@app.get("/invite/validate", response_model=schemas.InvitationValidate, tags=["Invitations"])
def validate_invitation(token: str, db: Session = Depends(get_db)):
    """
    Validate an invitation token.
    Returns user info if token is valid, otherwise raises error.
    """
    from app.auth import verify_invitation_token

    # Verify token
    payload = verify_invitation_token(token)

    # Check if user exists and invitation is still valid
    user = crud.get_user_by_email(db, email=payload["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been used"
        )

    if user.invitation_token != token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invitation token"
        )

    if user.invitation_expires_at and user.invitation_expires_at < datetime.datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has expired"
        )

    return schemas.InvitationValidate(
        email=payload["email"],
        full_name=payload["full_name"],
        expires_at=user.invitation_expires_at
    )


@app.post("/invite/accept", response_model=schemas.Token, tags=["Invitations"])
def accept_invitation(
    invitation_accept: schemas.InvitationAccept,
    db: Session = Depends(get_db)
):
    """
    Accept an invitation by setting password and activating account.
    Returns access token for immediate login.
    """
    from app.auth import verify_invitation_token, get_password_hash, create_access_token

    # Verify token
    payload = verify_invitation_token(invitation_accept.token)

    # Get user
    user = crud.get_user_by_email(db, email=payload["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been used"
        )

    if user.invitation_token != invitation_accept.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invitation token"
        )

    if user.invitation_expires_at and user.invitation_expires_at < datetime.datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has expired"
        )

    # Set password and activate user
    user.hashed_password = get_password_hash(invitation_accept.password)
    user.is_active = True
    user.invitation_token = None  # Clear token after use
    db.commit()
    db.refresh(user)

    # Create access token for immediate login
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# --- Query Endpoints ---
@app.post("/queries/", response_model=schemas.Query, status_code=201, tags=["Queries"])
def create_query(
    query: schemas.QueryCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Create a new query for the current user's active brand."""
    db_query = crud.get_query_by_query_id(db, query_id=query.query_id, user_id=current_user.id, brand_id=brand_id)
    if db_query:
        raise HTTPException(status_code=400, detail=f"Query ID {query.query_id} already exists for this brand")
    return crud.create_query(db=db, query=query, user_id=current_user.id, brand_id=brand_id)

@app.get("/queries/", response_model=List[schemas.Query], tags=["Queries"])
def read_queries(
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Retrieve a list of queries for the current user's active brand."""
    if active_only:
        queries = crud.get_active_queries(db, user_id=current_user.id, brand_id=brand_id, skip=skip, limit=limit)
    else:
        queries = crud.get_queries(db, user_id=current_user.id, brand_id=brand_id, skip=skip, limit=limit)
    return queries

@app.get("/queries/{query_id}", response_model=schemas.Query, tags=["Queries"])
def read_query(
    query_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Retrieve a single query by its user-facing ID (e.g., 'Q001') for the current user's active brand."""
    db_query = crud.get_query_by_query_id(db, query_id=query_id, user_id=current_user.id, brand_id=brand_id)
    if db_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return db_query

@app.put("/queries/{query_id}", response_model=schemas.Query, tags=["Queries"])
def update_query(
    query_id: str,
    query_update: schemas.QueryUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Update a query for the current user's active brand."""
    db_query = crud.update_query(db, query_id=query_id, query_update=query_update, user_id=current_user.id, brand_id=brand_id)
    if db_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return db_query

@app.delete("/queries/{query_id}", response_model=schemas.Query, tags=["Queries"])
def delete_query(
    query_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Delete a query for the current user's active brand."""
    deleted_query = crud.delete_query(db, query_id=query_id, user_id=current_user.id, brand_id=brand_id)
    if deleted_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return deleted_query


# --- Response Endpoints ---
@app.post("/responses/", response_model=schemas.Response, status_code=201, tags=["Responses"])
def create_response(
    response: schemas.ResponseCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Submit a raw response from an LLM platform for the current user's active brand."""
    return crud.create_response(db=db, response=response, user_id=current_user.id, brand_id=brand_id)

@app.get("/responses/", response_model=List[schemas.Response], tags=["Responses"])
def read_responses(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Retrieve a list of responses for the current user's active brand."""
    return crud.get_responses(db, user_id=current_user.id, brand_id=brand_id, skip=skip, limit=limit)

@app.get("/responses/unanalyzed/", response_model=List[schemas.Response], tags=["Responses"])
def read_unanalyzed_responses(
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve responses that are pending analysis for the current user."""
    return crud.get_unanalyzed_responses(db, user_id=current_user.id, limit=limit)

@app.put("/responses/{response_id}/analyze", response_model=schemas.Response, tags=["Responses"])
def update_response_analysis(
    response_id: int,
    analysis_data: schemas.ResponseAnalysisInput,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Update a response with analysis data for the current user's active brand."""
    db_response = crud.update_response_analysis(
        db,
        response_id=response_id,
        analysis_data=analysis_data.model_dump(exclude_unset=True),
        user_id=current_user.id,
        brand_id=brand_id
    )
    if db_response is None:
        raise HTTPException(status_code=404, detail="Response not found")
    return db_response

@app.delete("/responses/{response_id}", response_model=schemas.Response, tags=["Responses"])
def delete_response(
    response_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Delete a response for the current user's active brand."""
    deleted_response = crud.delete_response(db, response_id=response_id, user_id=current_user.id, brand_id=brand_id)
    if deleted_response is None:
        raise HTTPException(status_code=404, detail="Response not found")
    return deleted_response


# --- Competitor Endpoints ---
@app.post("/competitors/", response_model=schemas.Competitor, status_code=201, tags=["Competitors"])
def create_competitor(
    competitor: schemas.CompetitorCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Create a new competitor for the current user's active brand."""
    return crud.create_competitor(db=db, competitor=competitor, user_id=current_user.id, brand_id=brand_id)

@app.get("/competitors/", response_model=List[schemas.Competitor], tags=["Competitors"])
def read_competitors(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Retrieve a list of competitors for the current user's active brand."""
    return crud.get_competitors(db, user_id=current_user.id, brand_id=brand_id, skip=skip, limit=limit)

@app.put("/competitors/{competitor_id}", response_model=schemas.Competitor, tags=["Competitors"])
def update_competitor(
    competitor_id: int,
    competitor_update: schemas.CompetitorUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Update a competitor for the current user's active brand."""
    db_competitor = crud.update_competitor(
        db,
        competitor_id=competitor_id,
        competitor_update=competitor_update,
        user_id=current_user.id,
        brand_id=brand_id
    )
    if db_competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return db_competitor

@app.delete("/competitors/{competitor_id}", response_model=schemas.Competitor, tags=["Competitors"])
def delete_competitor(
    competitor_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Delete a competitor for the current user's active brand."""
    deleted_competitor = crud.delete_competitor(db, competitor_id=competitor_id, user_id=current_user.id, brand_id=brand_id)
    if deleted_competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return deleted_competitor


# --- Descriptor Endpoints ---
@app.post("/descriptors/", response_model=schemas.TargetDescriptor, status_code=201, tags=["Descriptors"])
def create_descriptor(
    descriptor: schemas.TargetDescriptorCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Create a new descriptor for the current user's active brand."""
    return crud.create_descriptor(db=db, descriptor=descriptor, user_id=current_user.id, brand_id=brand_id)

@app.get("/descriptors/", response_model=List[schemas.TargetDescriptor], tags=["Descriptors"])
def read_descriptors(
    target_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Retrieve a list of descriptors for the current user's active brand."""
    if target_only:
        return crud.get_target_descriptors(db, user_id=current_user.id, brand_id=brand_id, skip=skip, limit=limit)
    return crud.get_descriptors(db, user_id=current_user.id, brand_id=brand_id, skip=skip, limit=limit)

@app.get("/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor, tags=["Descriptors"])
def read_descriptor(
    descriptor_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Retrieve a single descriptor by its primary key for the current user's active brand."""
    db_descriptor = crud.get_descriptor(db, descriptor_id=descriptor_id, user_id=current_user.id, brand_id=brand_id)
    if db_descriptor is None:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return db_descriptor

@app.put("/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor, tags=["Descriptors"])
def update_descriptor(
    descriptor_id: int,
    descriptor_update: schemas.TargetDescriptorUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Update a descriptor for the current user's active brand."""
    db_descriptor = crud.update_descriptor(
        db,
        descriptor_id=descriptor_id,
        descriptor_update=descriptor_update,
        user_id=current_user.id,
        brand_id=brand_id
    )
    if db_descriptor is None:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return db_descriptor

@app.delete("/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor, tags=["Descriptors"])
def delete_descriptor(
    descriptor_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Delete a descriptor for the current user's active brand."""
    deleted_descriptor = crud.delete_descriptor(db, descriptor_id=descriptor_id, user_id=current_user.id, brand_id=brand_id)
    if deleted_descriptor is None:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return deleted_descriptor


# --- Report Endpoints ---
@app.post("/reports/", response_model=schemas.Report, status_code=201, tags=["Reports"])
def create_report(
    report: schemas.ReportCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new report for the current user."""
    return crud.create_report(db=db, report=report, user_id=current_user.id)

@app.get("/reports/", response_model=List[schemas.Report], tags=["Reports"])
def read_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a list of reports for the current user."""
    return crud.get_reports(db, user_id=current_user.id, skip=skip, limit=limit)

@app.get("/reports/{report_id}", response_model=schemas.Report, tags=["Reports"])
def read_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a single report by its ID for the current user."""
    db_report = crud.get_report(db, report_id=report_id, user_id=current_user.id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report

@app.put("/reports/{report_id}", response_model=schemas.Report, tags=["Reports"])
def update_report(
    report_id: int,
    report_update: schemas.ReportUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a report (mainly for adding Google Doc URL) for the current user."""
    db_report = crud.update_report(
        db,
        report_id=report_id,
        report_update=report_update,
        user_id=current_user.id
    )
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report


@app.delete("/reports/{report_id}", response_model=schemas.Report, tags=["Reports"])
def delete_report(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a report for the current user."""
    deleted_report = crud.delete_report(db, report_id=report_id, user_id=current_user.id)
    if deleted_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return deleted_report


@app.post("/reports/upload-charts", tags=["Reports"])
async def upload_chart_images(
    dashboard: Optional[str] = Form(None),
    sentiment: Optional[str] = Form(None),
    positioning: Optional[str] = Form(None),
    share_of_voice: Optional[str] = Form(None),
    timestamp: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Upload chart images (as base64 strings) and save them to disk with a predictable naming pattern.
    These will be used by report generation if available.
    """
    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found")

    # Create report_charts directory if it doesn't exist
    charts_dir = Path("frontend/public/report_charts")
    charts_dir.mkdir(parents=True, exist_ok=True)

    chart_paths = {}

    # Process each chart image with predictable naming
    charts_data = {
        'dashboard': dashboard,
        'sentiment': sentiment,
        'positioning': positioning,
        'share_of_voice': share_of_voice
    }

    for chart_name, base64_data in charts_data.items():
        if base64_data:
            try:
                # Remove the data:image/png;base64, prefix if present
                if ',' in base64_data:
                    base64_data = base64_data.split(',')[1]

                # Decode base64 to binary
                image_data = base64.b64decode(base64_data)

                # Create filename with predictable pattern that report generation can find
                # Format: {user_id}_{brand_id}_latest_{chart_name}.png
                filename = f"{current_user.id}_{brand_id}_latest_{chart_name}.png"
                filepath = charts_dir / filename

                # Write file
                with open(filepath, 'wb') as f:
                    f.write(image_data)

                # Store relative path for markdown
                chart_paths[chart_name] = f"report_charts/{filename}"

            except Exception as e:
                print(f"Error saving {chart_name} chart: {e}")
                continue

    return {
        "success": True,
        "chart_paths": chart_paths,
        "message": f"Uploaded {len(chart_paths)} chart(s) for report generation"
    }


@app.get("/reports/{report_id}/export/word", tags=["Reports"])
def export_report_to_word(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Export a report to Word document format with embedded charts."""
    from app.services.report_export import export_to_word_with_charts

    # Get the report
    db_report = crud.get_report(db, report_id=report_id, user_id=current_user.id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    # Generate Word document with charts
    word_file = export_to_word_with_charts(
        db_report.report_content,
        db_report.title,
        db,
        user_id=current_user.id,
        brand_id=brand_id
    )

    # Create safe filename
    safe_filename = "".join(c for c in db_report.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_filename}.docx"

    return StreamingResponse(
        word_file,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/reports/{report_id}/export/pdf", tags=["Reports"])
def export_report_to_pdf(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export a report to PDF format."""
    from app.services.report_export import export_to_pdf

    # Get the report
    db_report = crud.get_report(db, report_id=report_id, user_id=current_user.id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    # Generate PDF
    pdf_file = export_to_pdf(db_report.report_content, db_report.title)

    # Create safe filename
    safe_filename = "".join(c for c in db_report.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_filename}.pdf"

    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/reports/{report_id}/export/html", tags=["Reports"])
def export_report_to_html(
    report_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Export a report to interactive HTML with embedded Chart.js visualizations."""
    from app.services.report_html import generate_html_report_with_charts

    db_report = crud.get_report(db, report_id=report_id, user_id=current_user.id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    # Generate HTML with charts
    html_content = generate_html_report_with_charts(
        db_report.report_content,
        db_report.title,
        db,
        user_id=current_user.id,
        brand_id=brand_id
    )

    # Create safe filename
    safe_filename = "".join(c for c in db_report.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_filename}.html"

    return StreamingResponse(
        io.BytesIO(html_content.encode('utf-8')),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# --- Brand Info Endpoints ---
# --- Multi-Brand Endpoints ---

@app.get("/brands/", response_model=List[schemas.BrandInfoList], tags=["Brands"])
def get_all_brands_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all brands for the current user."""
    return crud.get_all_brands(db, user_id=current_user.id)

@app.get("/brands/active", response_model=schemas.BrandInfo, tags=["Brands"])
def get_active_brand_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the currently active brand for the user."""
    brand = crud.get_active_brand(db, user_id=current_user.id)
    if not brand:
        raise HTTPException(status_code=404, detail="No active brand found. Please create a brand first.")
    return brand

@app.get("/brands/{brand_id}", response_model=schemas.BrandInfo, tags=["Brands"])
def get_brand_endpoint(
    brand_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific brand by ID."""
    brand = crud.get_brand_by_id(db, brand_id=brand_id, user_id=current_user.id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@app.post("/brands/", response_model=schemas.BrandInfo, status_code=201, tags=["Brands"])
def create_brand_endpoint(
    brand_info: schemas.BrandInfoCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new brand (max 20 per user)."""
    try:
        return crud.create_brand_info(db, brand_info=brand_info, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/brands/{brand_id}", response_model=schemas.BrandInfo, tags=["Brands"])
def update_brand_endpoint(
    brand_id: int,
    brand_info: schemas.BrandInfoUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a specific brand."""
    updated_brand = crud.update_brand_info(db, brand_id=brand_id, brand_info_update=brand_info, user_id=current_user.id)
    if not updated_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return updated_brand

@app.post("/brands/{brand_id}/activate", response_model=schemas.BrandInfo, tags=["Brands"])
def activate_brand_endpoint(
    brand_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a brand as active (deactivates all other brands)."""
    brand = crud.activate_brand(db, brand_id=brand_id, user_id=current_user.id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@app.delete("/brands/{brand_id}", response_model=schemas.BrandInfo, tags=["Brands"])
def delete_brand_endpoint(
    brand_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a brand and all associated data."""
    deleted_brand = crud.delete_brand_info(db, brand_id=brand_id, user_id=current_user.id)
    if not deleted_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return deleted_brand

# --- Legacy Endpoints for Backward Compatibility ---

@app.get("/brand-info/", response_model=schemas.BrandInfo, tags=["Brand Info"])
def get_brand_info_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active brand info (legacy endpoint - use /brands/active instead)."""
    brand_info = crud.get_active_brand(db, user_id=current_user.id)
    if not brand_info:
        raise HTTPException(status_code=404, detail="Brand info not found. Please create it first.")
    return brand_info

@app.post("/brand-info/", response_model=schemas.BrandInfo, status_code=201, tags=["Brand Info"])
def create_brand_info_endpoint(
    brand_info: schemas.BrandInfoCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create brand info (legacy endpoint - use /brands/ instead)."""
    try:
        return crud.create_brand_info(db, brand_info=brand_info, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/brand-info/", response_model=schemas.BrandInfo, tags=["Brand Info"])
def update_brand_info_endpoint(
    brand_info: schemas.BrandInfoUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update active brand info (legacy endpoint)."""
    active_brand = crud.get_active_brand(db, user_id=current_user.id)
    if not active_brand:
        raise HTTPException(status_code=404, detail="No active brand found")
    updated_brand = crud.update_brand_info(db, brand_id=active_brand.id, brand_info_update=brand_info, user_id=current_user.id)
    if not updated_brand:
        raise HTTPException(status_code=404, detail="Brand info not found")
    return updated_brand

@app.delete("/brand-info/", response_model=schemas.BrandInfo, tags=["Brand Info"])
def delete_brand_info_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete active brand info (legacy endpoint)."""
    active_brand = crud.get_active_brand(db, user_id=current_user.id)
    if not active_brand:
        raise HTTPException(status_code=404, detail="No active brand found")
    deleted_brand = crud.delete_brand_info(db, brand_id=active_brand.id, user_id=current_user.id)
    if not deleted_brand:
        raise HTTPException(status_code=404, detail="Brand info not found")
    return deleted_brand


@app.post("/brand-info/generate", tags=["Brand Info"])
def generate_content_from_brand_info(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Generate queries, descriptors, and competitors based on active brand info using AI.
    This will replace any existing queries, descriptors, and competitors for the active brand.
    """
    from app.ai_generator import AIGenerator

    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found. Please select a brand first.")

    try:
        generator = AIGenerator(db)
        result = generator.generate_all(user_id=current_user.id, brand_id=brand_id)
        return {
            "message": "Content generated successfully",
            "queries_created": result["queries_created"],
            "descriptors_created": result["descriptors_created"],
            "competitors_created": result["competitors_created"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")


# --- Celery Task Trigger for the main weekly run ---
from celery_app.tasks import run_weekly_queries_task
@app.post("/tasks/trigger-weekly-run/", status_code=202, tags=["Tasks"])
async def trigger_weekly_run_endpoint():
    """Manually trigger the weekly query and analysis process."""
    task = run_weekly_queries_task.delay()
    return {"message": "Weekly run triggered.", "task_id": task.id}

@app.post("/tasks/trigger-analysis/", status_code=202, tags=["Tasks"])
async def trigger_analysis_on_unanalyzed(db: Session = Depends(get_db)):
    """Manually trigger analysis on all unanalyzed responses."""
    from celery_app.tasks import analyze_responses_batch_task
    unanalyzed_responses = crud.get_unanalyzed_responses(db, limit=1000)
    if not unanalyzed_responses:
        raise HTTPException(status_code=404, detail="No unanalyzed responses found.")

    response_ids = [resp.id for resp in unanalyzed_responses]
    task = analyze_responses_batch_task.delay(response_ids)
    return {"message": f"Analysis triggered for {len(response_ids)} responses.", "task_id": task.id}

# --- Direct Collection and Analysis Triggers (without Celery) ---
@app.post("/tasks/run-collection/", status_code=202, tags=["Tasks"])
async def run_collection(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Trigger response collection using the collection script for active brand."""
    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found. Please select a brand first.")

    # Get count of active queries
    query_count = db.query(models.Query).filter(
        models.Query.user_id == current_user.id,
        models.Query.brand_id == brand_id,
        models.Query.active == True
    ).count()

    if query_count == 0:
        raise HTTPException(status_code=400, detail="No active queries found for this brand.")

    # Create task status for collection
    task_status = models.TaskStatus(
        user_id=current_user.id,
        brand_id=brand_id,
        task_type="collection",
        status="running",
        total_items=query_count * 4,  # queries × 4 platforms
        processed_items=0,
        message="Starting collection..."
    )
    db.add(task_status)
    db.commit()
    db.refresh(task_status)

    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "collect_responses.py")
    try:
        # Run the collection script in the background with task-id
        cmd = [
            "python3", script_path,
            str(current_user.id),
            "--brand-id", str(brand_id),
            "--task-id", str(task_status.id)
        ]
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Send "1" to run all queries (auto-select option 1)
        process.stdin.write("1\n")
        process.stdin.flush()

        return {
            "message": "Response collection started for active brand.",
            "status": "running",
            "task_id": task_status.id,
            "note": "Collection is running in the background. Check the Responses page to see new data."
        }
    except Exception as e:
        task_status.status = "failed"
        task_status.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start collection: {str(e)}")

@app.post("/tasks/run-analysis/", status_code=202, tags=["Tasks"])
async def run_analysis(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Analyze responses from most recent collection date and auto-generate report for active brand."""
    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found. Please select a brand first.")

    # Find the most recent collection date for this brand
    most_recent_response = db.query(models.Response).filter(
        models.Response.user_id == current_user.id,
        models.Response.brand_id == brand_id
    ).order_by(models.Response.timestamp.desc()).first()

    if not most_recent_response:
        raise HTTPException(status_code=404, detail="No responses found for active brand.")

    # Get the date of the most recent collection (just the date part)
    latest_date = most_recent_response.timestamp.date()

    # Find all responses from that date
    latest_date_start = datetime.datetime.combine(latest_date, datetime.time.min)
    latest_date_end = latest_date_start + datetime.timedelta(days=1)

    responses_to_analyze = db.query(models.Response).filter(
        models.Response.user_id == current_user.id,
        models.Response.brand_id == brand_id,
        models.Response.timestamp >= latest_date_start,
        models.Response.timestamp < latest_date_end
    ).all()

    if not responses_to_analyze:
        raise HTTPException(status_code=404, detail="No responses found for the most recent collection date.")

    # Reset analysis fields for these responses
    for response in responses_to_analyze:
        response.analyzed_at = None
        response.brand_mentioned = None
        response.brand_position = None
        response.sentiment = None
        response.descriptors = None
        response.competitors = None
        response.sources = None

    db.commit()

    # Create task status for analysis
    task_status = models.TaskStatus(
        user_id=current_user.id,
        brand_id=brand_id,
        task_type="analysis_and_report",
        status="running",
        total_items=len(responses_to_analyze),
        processed_items=0,
        message=f"Analyzing {len(responses_to_analyze)} responses from {latest_date.strftime('%Y-%m-%d')}..."
    )
    db.add(task_status)
    db.commit()
    db.refresh(task_status)

    analysis_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analyze_responses.py")
    report_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generate_report.py")

    try:
        # Get the project root directory (where tales.db is located)
        project_root = os.path.dirname(os.path.dirname(__file__))

        # Run analysis and report generation in sequence in the background with task-id
        cmd = f"""
python3 {analysis_script} --all --user-id {current_user.id} --brand-id {brand_id} --task-id {task_status.id} &&
python3 {report_script} --user-id {current_user.id} --brand-id {brand_id}
"""
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_root
        )

        return {
            "message": f"Analysis and report generation started for {len(responses_to_analyze)} responses from {latest_date.strftime('%Y-%m-%d')}.",
            "status": "running",
            "task_id": task_status.id,
            "count": len(responses_to_analyze),
            "note": "Analyzing latest data and generating report. This will update all analytics pages."
        }
    except Exception as e:
        task_status.status = "failed"
        task_status.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@app.post("/tasks/rerun-analysis/", status_code=202, tags=["Tasks"])
async def rerun_analysis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Reset analysis on responses for active brand (optionally filtered by date range) and regenerate report."""
    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found. Please select a brand first.")

    # Build query for responses
    query = db.query(models.Response).filter(
        models.Response.user_id == current_user.id,
        models.Response.brand_id == brand_id
    )

    # Apply date filters if provided
    date_description = "all"
    if start_date:
        try:
            start_dt = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(models.Response.timestamp >= start_dt)
            date_description = f"from {start_date[:10]}"
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format (YYYY-MM-DD).")

    if end_date:
        try:
            end_dt = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # Add one day to include the entire end date
            end_dt = end_dt + datetime.timedelta(days=1)
            query = query.filter(models.Response.timestamp < end_dt)
            if start_date:
                date_description = f"from {start_date[:10]} to {end_date[:10]}"
            else:
                date_description = f"through {end_date[:10]}"
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format (YYYY-MM-DD).")

    all_responses = query.all()

    if not all_responses:
        raise HTTPException(status_code=404, detail=f"No responses found for active brand {date_description}.")

    # Reset analyzed_at to NULL for filtered responses (marks them as unanalyzed)
    for response in all_responses:
        response.analyzed_at = None
        # Clear existing analysis fields so they get fresh analysis
        response.brand_mentioned = None
        response.brand_position = None
        response.sentiment = None
        response.descriptors = None
        response.competitors = None
        response.sources = None

    db.commit()

    # Create task status for re-analysis
    message = f"Re-analyzing {len(all_responses)} responses {date_description}..."
    task_status = models.TaskStatus(
        user_id=current_user.id,
        brand_id=brand_id,
        task_type="analysis_and_report",
        status="running",
        total_items=len(all_responses),
        processed_items=0,
        message=message,
        started_at=datetime.datetime.utcnow()
    )
    db.add(task_status)
    db.commit()
    db.refresh(task_status)

    analysis_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analyze_responses.py")
    report_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generate_report.py")

    try:
        # Get the project root directory (where tales.db is located)
        project_root = os.path.dirname(os.path.dirname(__file__))

        # Run analysis and report generation in sequence in the background
        cmd = f"""
python3 {analysis_script} --all --user-id {current_user.id} --brand-id {brand_id} --task-id {task_status.id} &&
python3 {report_script} --user-id {current_user.id} --brand-id {brand_id}
"""
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_root
        )

        return {
            "message": f"Re-analysis started for {len(all_responses)} responses {date_description}.",
            "status": "running",
            "task_id": task_status.id,
            "count": len(all_responses),
            "date_range": date_description,
            "note": "Re-analyzing responses with updated analysis process. A new report will be generated when complete."
        }
    except Exception as e:
        task_status.status = "failed"
        task_status.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start re-analysis: {str(e)}")

@app.get("/tasks/status/", response_model=Optional[schemas.TaskStatus], tags=["Tasks"])
def get_task_status(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Get the status of the most recent task for the active brand."""
    if not brand_id:
        return None

    # Get the most recent task for this user and brand
    task = db.query(models.TaskStatus).filter(
        models.TaskStatus.user_id == current_user.id,
        models.TaskStatus.brand_id == brand_id
    ).order_by(models.TaskStatus.started_at.desc()).first()

    if not task:
        return None

    # Check if the task is still running by checking unanalyzed responses
    if task.status == "running":
        unanalyzed = crud.get_unanalyzed_responses(db, user_id=current_user.id, brand_id=brand_id, limit=1)
        if not unanalyzed and task.task_type == "analysis_and_report":
            # Analysis is complete, check if we're generating report
            # For simplicity, mark as completed if no unanalyzed responses
            task.status = "completed"
            task.completed_at = datetime.datetime.utcnow()
            task.message = "Analysis and report generation completed"
            db.commit()
            db.refresh(task)

    return task
