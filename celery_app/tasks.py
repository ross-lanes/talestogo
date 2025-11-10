import datetime
import logging
from celery import group, chord
from .celery import app as celery_app
from app.database import SessionLocal
from app import crud, schemas, models
from app.services.llm_service import query_platform_api, analyze_raw_response
from typing import List
from sqlalchemy import and_

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

        # Use the CRUD function to create the response with proper user_id and brand_id
        response_schema = schemas.ResponseCreate(
            query_id=query.query_id,
            query_text=query.query_text,
            platform=platform,
            response_text=raw_response_text
            # The timestamp is now set by the model's default value
        )
        db_response = crud.create_response(
            db,
            response=response_schema,
            user_id=query.user_id,
            brand_id=query.brand_id
        )
        logger.info(f"Successfully saved response for {query.query_id} (user={query.user_id}, brand={query.brand_id}) on {platform}")
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
        # Get a batch of unanalyzed responses
        responses_to_analyze = crud.get_responses_by_ids(db, response_ids=response_ids)

        if not responses_to_analyze:
            logger.info(f"No responses found for IDs: {response_ids}")
            return f"No responses found for IDs: {response_ids}"

        logger.info(f"Found {len(responses_to_analyze)} responses to analyze.")

        # Get user_id and brand_id from the first response for filtering
        # All responses in a batch should belong to the same user and brand
        first_response = responses_to_analyze[0]
        user_id = first_response.user_id
        brand_id = first_response.brand_id

        logger.info(f"Analyzing responses for user_id={user_id}, brand_id={brand_id}")

        # Get context data filtered by user and brand
        competitors = [c.organization for c in crud.get_competitors(db, user_id=user_id, brand_id=brand_id, limit=1000)]
        descriptors = [d.descriptor for d in crud.get_target_descriptors(db, user_id=user_id, brand_id=brand_id, limit=1000)]

        if not competitors or not descriptors:
            logger.warning(f"No competitors or target descriptors found for user {user_id}, brand {brand_id}. Analysis may be inaccurate.")

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
    It fetches all active queries FOR ALL USERS AND BRANDS and dispatches individual tasks for each platform.
    """
    logger.info("--- Starting weekly query run ---")
    db = SessionLocal()
    try:
        # Get all active queries across all users and brands
        # Query the database directly since CRUD functions require user_id
        active_queries = db.query(models.Query).filter(
            models.Query.active == True
        ).limit(1000).all()

        if not active_queries:
            logger.info("No active queries found. Weekly run complete.")
            return "No active queries."

        logger.info(f"Found {len(active_queries)} active queries to process across all users/brands.")

        platforms = ["Perplexity", "Claude", "Gemini"]

        # Group queries by user and brand for proper analysis batching
        # We need to analyze each user/brand separately with their own competitors/descriptors
        queries_by_brand = {}
        for query in active_queries:
            key = (query.user_id, query.brand_id)
            if key not in queries_by_brand:
                queries_by_brand[key] = []
            queries_by_brand[key].append(query)

        logger.info(f"Processing {len(queries_by_brand)} unique user/brand combinations")

        # Create separate chords for each user/brand combination
        for (user_id, brand_id), brand_queries in queries_by_brand.items():
            logger.info(f"Dispatching tasks for user_id={user_id}, brand_id={brand_id}: {len(brand_queries)} queries")

            # Create a chord for this user/brand's queries
            callback = analyze_responses_batch_task.s()
            task_chord = chord(
                query_llm_platform_task.s(query_pk=query.id, platform=platform)
                for query in brand_queries
                for platform in platforms
            )(callback)

            # Schedule this chord
            task_chord.apply_async()

            logger.info(f"Dispatched chord for user_id={user_id}, brand_id={brand_id}: {len(brand_queries) * len(platforms)} query tasks")

    finally:
        db.close()

    return f"Successfully dispatched chords for {len(active_queries)} total queries across {len(queries_by_brand)} user/brand combinations."


@celery_app.task(bind=True)
def check_and_run_scheduled_tasks(self):
    """
    Daily task that checks for scheduled tasks that are due to run.
    Looks at the next_run_at field and triggers collection for brands that are due.
    """
    logger.info("--- Checking for scheduled tasks to run ---")
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()

        # Get all enabled scheduled tasks where next_run_at is in the past
        due_tasks = db.query(models.ScheduledTask).filter(
            and_(
                models.ScheduledTask.is_enabled == True,
                models.ScheduledTask.next_run_at <= now
            )
        ).all()

        if not due_tasks:
            logger.info("No scheduled tasks due to run.")
            return "No scheduled tasks due."

        logger.info(f"Found {len(due_tasks)} scheduled tasks due to run")

        for task in due_tasks:
            logger.info(f"Running scheduled task for user_id={task.user_id}, brand_id={task.brand_id}, schedule_type={task.schedule_type}")

            try:
                # Get active queries for this user and brand
                active_queries = crud.get_active_queries(db, user_id=task.user_id, brand_id=task.brand_id, limit=1000)

                if not active_queries:
                    logger.warning(f"No active queries for user_id={task.user_id}, brand_id={task.brand_id}")
                    continue

                platforms = ["Perplexity", "Claude", "Gemini"]

                # Create a chord for this brand's queries with analysis callback
                callback = analyze_responses_batch_task.s()
                task_chord = chord(
                    query_llm_platform_task.s(query_pk=query.id, platform=platform)
                    for query in active_queries
                    for platform in platforms
                )(callback)

                # Schedule this chord
                task_chord.apply_async()

                # Update last_run_at
                task.last_run_at = now

                # Calculate next_run_at based on schedule_type
                if task.schedule_type == 'first_day':
                    # Next month, 1st day
                    if now.month == 12:
                        next_run = datetime.datetime(now.year + 1, 1, 1, 10, 0, 0)
                    else:
                        next_run = datetime.datetime(now.year, now.month + 1, 1, 10, 0, 0)
                elif task.schedule_type == 'middle':
                    # Next month, 15th day
                    if now.month == 12:
                        next_run = datetime.datetime(now.year + 1, 1, 15, 10, 0, 0)
                    else:
                        next_run = datetime.datetime(now.year, now.month + 1, 15, 10, 0, 0)
                elif task.schedule_type == 'last_day':
                    # Last day of next month
                    if now.month == 12:
                        next_month = datetime.datetime(now.year + 1, 1, 1)
                    else:
                        next_month = datetime.datetime(now.year, now.month + 1, 1)
                    # Get last day by going to first of following month and subtracting 1 day
                    if next_month.month == 12:
                        first_of_following = datetime.datetime(next_month.year + 1, 1, 1)
                    else:
                        first_of_following = datetime.datetime(next_month.year, next_month.month + 1, 1)
                    last_day_of_next_month = first_of_following - datetime.timedelta(days=1)
                    next_run = datetime.datetime(last_day_of_next_month.year, last_day_of_next_month.month, last_day_of_next_month.day, 10, 0, 0)
                else:
                    logger.error(f"Unknown schedule_type: {task.schedule_type}")
                    continue

                task.next_run_at = next_run
                db.commit()

                logger.info(f"Scheduled task dispatched for user_id={task.user_id}, brand_id={task.brand_id}. Next run: {next_run}")

                # Create history record
                history = models.ScheduledTaskHistory(
                    scheduled_task_id=task.id,
                    user_id=task.user_id,
                    brand_id=task.brand_id,
                    started_at=now,
                    status='running',
                    collection_responses=len(active_queries) * len(platforms)
                )
                db.add(history)
                db.commit()

            except Exception as e:
                logger.error(f"Failed to run scheduled task for user_id={task.user_id}, brand_id={task.brand_id}: {e}", exc_info=True)
                continue

        return f"Triggered {len(due_tasks)} scheduled tasks"

    finally:
        db.close()
