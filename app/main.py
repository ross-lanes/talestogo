from dotenv import load_dotenv
load_dotenv(override=True)  # Load environment variables from .env file

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta
import os
import subprocess

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
    get_or_create_oauth_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# This line ensures tables are created if they don't exist when the app starts.
# It's convenient for development. For production, you'd use a migration tool.
models.Base.metadata.create_all(bind=engine)

# Create the FastAPI app instance
app = FastAPI(
    title="AIRO API - AI Reputation Optimizer",
    description="API for tracking and analyzing LLM depictions of PPPL.",
    version="0.1.0"
)

# Configure CORS to allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(analytics.router)

# --- Dependency ---
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

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint to check if the API is running."""
    return {"message": "Welcome to the AIRO API!"}


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


# --- Query Endpoints ---
@app.post("/queries/", response_model=schemas.Query, status_code=201, tags=["Queries"])
def create_query(
    query: schemas.QueryCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new query for the current user."""
    db_query = crud.get_query_by_query_id(db, query_id=query.query_id, user_id=current_user.id)
    if db_query:
        raise HTTPException(status_code=400, detail=f"Query ID {query.query_id} already exists for this user")
    return crud.create_query(db=db, query=query, user_id=current_user.id)

@app.get("/queries/", response_model=List[schemas.Query], tags=["Queries"])
def read_queries(
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a list of queries for the current user."""
    if active_only:
        queries = crud.get_active_queries(db, user_id=current_user.id, skip=skip, limit=limit)
    else:
        queries = crud.get_queries(db, user_id=current_user.id, skip=skip, limit=limit)
    return queries

@app.get("/queries/{query_id}", response_model=schemas.Query, tags=["Queries"])
def read_query(
    query_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a single query by its user-facing ID (e.g., 'Q001') for the current user."""
    db_query = crud.get_query_by_query_id(db, query_id=query_id, user_id=current_user.id)
    if db_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return db_query

@app.put("/queries/{query_id}", response_model=schemas.Query, tags=["Queries"])
def update_query(
    query_id: str,
    query_update: schemas.QueryUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a query for the current user."""
    db_query = crud.update_query(db, query_id=query_id, query_update=query_update, user_id=current_user.id)
    if db_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return db_query

@app.delete("/queries/{query_id}", response_model=schemas.Query, tags=["Queries"])
def delete_query(
    query_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a query for the current user."""
    deleted_query = crud.delete_query(db, query_id=query_id, user_id=current_user.id)
    if deleted_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return deleted_query


# --- Response Endpoints ---
@app.post("/responses/", response_model=schemas.Response, status_code=201, tags=["Responses"])
def create_response(
    response: schemas.ResponseCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a raw response from an LLM platform for the current user."""
    return crud.create_response(db=db, response=response, user_id=current_user.id)

@app.get("/responses/", response_model=List[schemas.Response], tags=["Responses"])
def read_responses(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a list of responses for the current user."""
    return crud.get_responses(db, user_id=current_user.id, skip=skip, limit=limit)

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
    db: Session = Depends(get_db)
):
    """Update a response with analysis data for the current user."""
    db_response = crud.update_response_analysis(
        db,
        response_id=response_id,
        analysis_data=analysis_data.model_dump(exclude_unset=True),
        user_id=current_user.id
    )
    if db_response is None:
        raise HTTPException(status_code=404, detail="Response not found")
    return db_response

@app.delete("/responses/{response_id}", response_model=schemas.Response, tags=["Responses"])
def delete_response(
    response_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a response for the current user."""
    deleted_response = crud.delete_response(db, response_id=response_id, user_id=current_user.id)
    if deleted_response is None:
        raise HTTPException(status_code=404, detail="Response not found")
    return deleted_response


# --- Competitor Endpoints ---
@app.post("/competitors/", response_model=schemas.Competitor, status_code=201, tags=["Competitors"])
def create_competitor(
    competitor: schemas.CompetitorCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new competitor for the current user."""
    return crud.create_competitor(db=db, competitor=competitor, user_id=current_user.id)

@app.get("/competitors/", response_model=List[schemas.Competitor], tags=["Competitors"])
def read_competitors(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a list of competitors for the current user."""
    return crud.get_competitors(db, user_id=current_user.id, skip=skip, limit=limit)

@app.put("/competitors/{competitor_id}", response_model=schemas.Competitor, tags=["Competitors"])
def update_competitor(
    competitor_id: int,
    competitor_update: schemas.CompetitorUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a competitor for the current user."""
    db_competitor = crud.update_competitor(
        db,
        competitor_id=competitor_id,
        competitor_update=competitor_update,
        user_id=current_user.id
    )
    if db_competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return db_competitor

@app.delete("/competitors/{competitor_id}", response_model=schemas.Competitor, tags=["Competitors"])
def delete_competitor(
    competitor_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a competitor for the current user."""
    deleted_competitor = crud.delete_competitor(db, competitor_id=competitor_id, user_id=current_user.id)
    if deleted_competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return deleted_competitor


# --- Descriptor Endpoints ---
@app.post("/descriptors/", response_model=schemas.TargetDescriptor, status_code=201, tags=["Descriptors"])
def create_descriptor(
    descriptor: schemas.TargetDescriptorCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new descriptor for the current user."""
    return crud.create_descriptor(db=db, descriptor=descriptor, user_id=current_user.id)

@app.get("/descriptors/", response_model=List[schemas.TargetDescriptor], tags=["Descriptors"])
def read_descriptors(
    target_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a list of descriptors for the current user."""
    if target_only:
        return crud.get_target_descriptors(db, user_id=current_user.id, skip=skip, limit=limit)
    return crud.get_descriptors(db, user_id=current_user.id, skip=skip, limit=limit)

@app.get("/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor, tags=["Descriptors"])
def read_descriptor(
    descriptor_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a single descriptor by its primary key for the current user."""
    db_descriptor = crud.get_descriptor(db, descriptor_id=descriptor_id, user_id=current_user.id)
    if db_descriptor is None:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return db_descriptor

@app.put("/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor, tags=["Descriptors"])
def update_descriptor(
    descriptor_id: int,
    descriptor_update: schemas.TargetDescriptorUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a descriptor for the current user."""
    db_descriptor = crud.update_descriptor(
        db,
        descriptor_id=descriptor_id,
        descriptor_update=descriptor_update,
        user_id=current_user.id
    )
    if db_descriptor is None:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return db_descriptor

@app.delete("/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor, tags=["Descriptors"])
def delete_descriptor(
    descriptor_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a descriptor for the current user."""
    deleted_descriptor = crud.delete_descriptor(db, descriptor_id=descriptor_id, user_id=current_user.id)
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
    db: Session = Depends(get_db)
):
    """
    Generate queries, descriptors, and competitors based on brand info using AI.
    This will replace any existing queries, descriptors, and competitors.
    """
    from app.ai_generator import AIGenerator

    try:
        generator = AIGenerator(db)
        result = generator.generate_all(user_id=current_user.id)
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
async def run_collection(current_user: models.User = Depends(get_current_user)):
    """Trigger response collection using the collection script."""
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "collect_responses.py")
    try:
        # Run the collection script in the background with user_id as argument
        process = subprocess.Popen(
            ["python3", script_path, str(current_user.id)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Send "1" to run all queries (auto-select option 1)
        process.stdin.write("1\n")
        process.stdin.flush()

        return {
            "message": "Response collection started.",
            "status": "running",
            "note": "Collection is running in the background. Check the Responses page to see new data."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start collection: {str(e)}")

@app.post("/tasks/run-analysis/", status_code=202, tags=["Tasks"])
async def run_analysis(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger analysis on unanalyzed responses using the analysis script."""
    unanalyzed_responses = crud.get_unanalyzed_responses(db, user_id=current_user.id, limit=1000)
    if not unanalyzed_responses:
        raise HTTPException(status_code=404, detail="No unanalyzed responses found.")

    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analyze_responses.py")

    try:
        # Run the analysis script in the background with --all flag
        process = subprocess.Popen(
            ["python3", script_path, "--all"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return {
            "message": f"Analysis started for {len(unanalyzed_responses)} responses.",
            "status": "running",
            "count": len(unanalyzed_responses),
            "note": "Analysis is running in the background using Gemini AI. Check the Dashboard to see updated metrics."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")
