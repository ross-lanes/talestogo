import datetime
import logging
from celery import group, chord
from .celery import app as celery_app
from app.database import SessionLocal
from app import crud, schemas, models
from app.services.llm_service import query_platform_api, analyze_raw_response
from typing import List

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def query_llm_platform_task(self, query_pk: int, platform: str):
    """
    Celery task to query a single LLM platform and save the raw response.
    Accepts the primary key of the query to reduce argument size.
    """
    db = SessionLocal()
    try:
        # Fetch the query object using its primary key
        query = crud.get_query(db, query_id_internal=query_pk)
        if not query:
            logger.warning(f"Query with PK {query_pk} not found. Skipping task.")
            return

        logger.info(f"Executing task for Query ID: {query.query_id} on Platform: {platform}")

        # Call the API service function
        raw_response_text = query_platform_api(query.query_text, platform)

        # Use the CRUD function to create the response
        response_schema = schemas.ResponseCreate(
            query_id=query.query_id,
            query_text=query.query_text,
            platform=platform,
            response_text=raw_response_text
            # The timestamp is now set by the model's default value
        )
        db_response = crud.create_response(db, response=response_schema)
        logger.info(f"Successfully saved response for {query.query_id} on {platform}")
        # Return the ID of the created response object for the chord
        return db_response.id

    except Exception as exc:
        # Use query.query_id if available for better logging
        query_identifier = query.query_id if 'query' in locals() and query else f"PK {query_pk}"
        logger.error(f"Task failed for {query_identifier} on {platform}: {exc}", exc_info=True)
        # Retry the task with an exponential backoff
        self.retry(exc=exc)
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def analyze_responses_batch_task(self, response_ids: List[int]):
    """
    Analyzes a batch of raw responses and saves the structured data.
    """
    logger.info("--- Starting analysis batch task ---")
    db = SessionLocal() 
    try:
        # Get context data first
        competitors = [c.organization for c in crud.get_competitors(db, limit=1000)]
        descriptors = [d.descriptor for d in crud.get_target_descriptors(db, limit=1000)]

        if not competitors or not descriptors:
            logger.warning("No competitors or target descriptors found in the database. Analysis may be inaccurate.")

        # Get a batch of unanalyzed responses
        responses_to_analyze = crud.get_responses_by_ids(db, response_ids=response_ids)
        
        if not responses_to_analyze:
            logger.info(f"No responses found for IDs: {response_ids}")
            return f"No responses found for IDs: {response_ids}"

        logger.info(f"Found {len(responses_to_analyze)} responses to analyze.")

        for response in responses_to_analyze:
            logger.info(f"Analyzing response ID: {response.id} for query '{response.query_id}'...")
            try:
                # Call the analysis service function
                analysis_result = analyze_raw_response(
                    query_text=response.query_text,
                    response_text=response.response_text,
                    competitors=competitors,
                    descriptors=descriptors
                )
                
                # Update the response in the database with the structured analysis
                if "error" not in analysis_result:
                    # The service already returns a dict with string values, which matches the model, not the Pydantic schema for input
                    crud.update_response_analysis(db, response_id=response.id, analysis_data=analysis_result)
                    logger.info(f"Successfully analyzed response ID: {response.id}")
                else:
                    logger.error(f"Failed to analyze response ID: {response.id}. Reason: {analysis_result['error']}")
                    # Optionally, mark it as failed in the DB
                    crud.update_response_analysis(db, response_id=response.id, analysis_data={"notes": f"Analysis failed: {analysis_result['error']}"})

            except Exception as e:
                logger.error(f"An unexpected error occurred while analyzing response ID {response.id}: {e}", exc_info=True)
                # Continue to the next response

        return f"Analyzed {len(responses_to_analyze)} responses."

    except Exception as exc:
        logger.error(f"Analysis batch task failed critically: {exc}", exc_info=True)
        self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True)
def run_weekly_queries_task(self):
    """
    The main task scheduled to run weekly.
    It fetches all active queries and dispatches individual tasks for each platform.
    """
    logger.info("--- Starting weekly query run ---")
    db = SessionLocal()
    try:
        active_queries = crud.get_active_queries(db, limit=1000) # Get all active queries
        if not active_queries:
            logger.info("No active queries found. Weekly run complete.")
            return "No active queries."

        logger.info(f"Found {len(active_queries)} active queries to process.")
        
        platforms = ["Perplexity", "Claude", "Gemini"]
        
        # Create a group of tasks to run in parallel
        # A chord will execute the analysis task only after all query tasks are complete.
        callback = analyze_responses_batch_task.s()
        task_chord = chord(
            query_llm_platform_task.s(query_pk=query.id, platform=platform)
            for query in active_queries
            for platform in platforms
        )(callback)

        # The chord must be called with apply_async() to be scheduled.
        task_chord.apply_async()

        logger.info(f"Dispatched a chord of {len(active_queries) * len(platforms)} query tasks with an analysis callback.")
        
    finally:
        db.close()

    return f"Successfully dispatched chord for {len(active_queries)} queries."
