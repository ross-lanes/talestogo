from dotenv import load_dotenv
load_dotenv(override=True)  # Load environment variables from .env file

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import engine

# Import all routers
from app.routers import (
    analytics,
    admin,
    batches,
    scheduled_tasks,
    help,
    tasks,
    auth,
    users,
    queries,
    responses,
    competitors,
    descriptors,
    reports,
    brands,
    operations,
    tenants,
    personas  # Heads - Persona Intelligence Platform
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

# Import for exception handling
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException

# Add exception handler to ensure CORS headers on all responses
@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    """Add CORS headers to error responses"""
    origin = request.headers.get("origin")

    # List of allowed origins (must match CORS config)
    allowed_origins = [
        "http://localhost:5173",
        "https://tales-frontend.onrender.com",
        "https://tales.robotrachel.com",
        "https://solsticehc.robotrachel.com",
        "https://api.tales.robotrachel.com",
    ]

    headers = {}
    if origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers
    )

# Configure CORS to allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "https://tales-frontend.onrender.com",  # Production frontend (legacy)
        "https://tales.robotrachel.com",  # Production frontend (custom domain)
        "https://solsticehc.robotrachel.com",  # Solstice HC tenant subdomain
        "https://api.tales.robotrachel.com",  # API subdomain
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include all routers
# Core functionality routers
app.include_router(auth.router)
app.include_router(users.admin_router)
app.include_router(users.invitation_router)
app.include_router(tenants.router)
app.include_router(queries.router)
app.include_router(responses.router)
app.include_router(competitors.router)
app.include_router(descriptors.router)
app.include_router(brands.router_brands)
app.include_router(brands.router_brand_info)
app.include_router(reports.router)
app.include_router(reports.how_tales_works_router)
app.include_router(operations.router)

# Heads - Persona Intelligence Platform
app.include_router(personas.router)

# Analytics and admin routers
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(batches.router)
app.include_router(scheduled_tasks.router)
app.include_router(help.router)
app.include_router(tasks.router)

# --- Scheduler ---
from app.scheduler import start_scheduler, stop_scheduler

@app.on_event("startup")
async def startup_event():
    """Start the background scheduler when the app starts"""
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the background scheduler when the app shuts down"""
    stop_scheduler()

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint to check if the API is running."""
    return {"message": "Welcome to the TALES API!"}
