from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import subprocess

# Use explicit imports from the 'app' package
from app import crud, models, schemas
from app.database import SessionLocal, engine
from app.routers import analytics

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


# --- Query Endpoints ---
@app.post("/queries/", response_model=schemas.Query, status_code=201, tags=["Queries"])
def create_query(query: schemas.QueryCreate, db: Session = Depends(get_db)):
    """Create a new query."""
    db_query = crud.get_query_by_query_id(db, query_id=query.query_id)
    if db_query:
        raise HTTPException(status_code=400, detail=f"Query ID {query.query_id} already registered")
    return crud.create_query(db=db, query=query)

@app.get("/queries/", response_model=List[schemas.Query], tags=["Queries"])
def read_queries(active_only: bool = False, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve a list of queries."""
    if active_only:
        queries = crud.get_active_queries(db, skip=skip, limit=limit)
    else:
        queries = crud.get_queries(db, skip=skip, limit=limit)
    return queries

@app.get("/queries/{query_id}", response_model=schemas.Query, tags=["Queries"])
def read_query(query_id: str, db: Session = Depends(get_db)):
    """Retrieve a single query by its user-facing ID (e.g., 'Q001')."""
    db_query = crud.get_query_by_query_id(db, query_id=query_id)
    if db_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return db_query

@app.put("/queries/{query_id}", response_model=schemas.Query, tags=["Queries"])
def update_query(query_id: str, query_update: schemas.QueryUpdate, db: Session = Depends(get_db)):
    """Update a query."""
    db_query = crud.update_query(db, query_id=query_id, query_update=query_update)
    if db_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return db_query

@app.delete("/queries/{query_id}", response_model=schemas.Query, tags=["Queries"])
def delete_query(query_id: str, db: Session = Depends(get_db)):
    """Delete a query."""
    deleted_query = crud.delete_query(db, query_id=query_id)
    if deleted_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return deleted_query


# --- Response Endpoints ---
@app.post("/responses/", response_model=schemas.Response, status_code=201, tags=["Responses"])
def create_response(response: schemas.ResponseCreate, db: Session = Depends(get_db)):
    """Submit a raw response from an LLM platform."""
    return crud.create_response(db=db, response=response)

@app.get("/responses/", response_model=List[schemas.Response], tags=["Responses"])
def read_responses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve a list of responses."""
    return crud.get_responses(db, skip=skip, limit=limit)
    
@app.get("/responses/unanalyzed/", response_model=List[schemas.Response], tags=["Responses"])
def read_unanalyzed_responses(limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve responses that are pending analysis."""
    return crud.get_unanalyzed_responses(db, limit=limit)

@app.put("/responses/{response_id}/analyze", response_model=schemas.Response, tags=["Responses"])
def update_response_analysis(response_id: int, analysis_data: schemas.ResponseAnalysisInput, db: Session = Depends(get_db)):
    """Update a response with analysis data."""
    db_response = crud.update_response_analysis(db, response_id=response_id, analysis_data=analysis_data)
    if db_response is None:
        raise HTTPException(status_code=404, detail="Response not found")
    return db_response


# --- Competitor Endpoints ---
@app.post("/competitors/", response_model=schemas.Competitor, status_code=201, tags=["Competitors"])
def create_competitor(competitor: schemas.CompetitorCreate, db: Session = Depends(get_db)):
    """Create a new competitor."""
    return crud.create_competitor(db=db, competitor=competitor)

@app.get("/competitors/", response_model=List[schemas.Competitor], tags=["Competitors"])
def read_competitors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve a list of competitors."""
    return crud.get_competitors(db, skip=skip, limit=limit)

@app.put("/competitors/{competitor_id}", response_model=schemas.Competitor, tags=["Competitors"])
def update_competitor(competitor_id: int, competitor_update: schemas.CompetitorUpdate, db: Session = Depends(get_db)):
    """Update a competitor."""
    db_competitor = crud.update_competitor(db, competitor_id=competitor_id, competitor_update=competitor_update)
    if db_competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return db_competitor

@app.delete("/competitors/{competitor_id}", response_model=schemas.Competitor, tags=["Competitors"])
def delete_competitor(competitor_id: int, db: Session = Depends(get_db)):
    """Delete a competitor."""
    deleted_competitor = crud.delete_competitor(db, competitor_id=competitor_id)
    if deleted_competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return deleted_competitor


# --- Descriptor Endpoints ---
@app.post("/descriptors/", response_model=schemas.TargetDescriptor, status_code=201, tags=["Descriptors"])
def create_descriptor(descriptor: schemas.TargetDescriptorCreate, db: Session = Depends(get_db)):
    """Create a new descriptor."""
    return crud.create_descriptor(db=db, descriptor=descriptor)

@app.get("/descriptors/", response_model=List[schemas.TargetDescriptor], tags=["Descriptors"])
def read_descriptors(target_only: bool = False, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve a list of descriptors."""
    if target_only:
        return crud.get_target_descriptors(db, skip=skip, limit=limit)
    return crud.get_descriptors(db, skip=skip, limit=limit)

@app.get("/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor, tags=["Descriptors"])
def read_descriptor(descriptor_id: int, db: Session = Depends(get_db)):
    """Retrieve a single descriptor by its primary key."""
    db_descriptor = crud.get_descriptor(db, descriptor_id=descriptor_id)
    if db_descriptor is None:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return db_descriptor

@app.put("/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor, tags=["Descriptors"])
def update_descriptor(descriptor_id: int, descriptor_update: schemas.TargetDescriptorUpdate, db: Session = Depends(get_db)):
    """Update a descriptor."""
    db_descriptor = crud.update_descriptor(db, descriptor_id=descriptor_id, descriptor_update=descriptor_update)
    if db_descriptor is None:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return db_descriptor

@app.delete("/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor, tags=["Descriptors"])
def delete_descriptor(descriptor_id: int, db: Session = Depends(get_db)):
    """Delete a descriptor."""
    deleted_descriptor = crud.delete_descriptor(db, descriptor_id=descriptor_id)
    if deleted_descriptor is None:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return deleted_descriptor


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
async def run_collection():
    """Trigger response collection using the collection script."""
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "collect_responses.py")
    try:
        # Run the collection script in the background
        process = subprocess.Popen(
            ["python3", script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Send "1" to run all queries
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
async def run_analysis(db: Session = Depends(get_db)):
    """Trigger analysis on unanalyzed responses using the analysis script."""
    unanalyzed_responses = crud.get_unanalyzed_responses(db, limit=1000)
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
