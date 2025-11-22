import os
from celery import Celery
from dotenv import load_dotenv
from celery.schedules import crontab

# --- Celery Application Setup ---
# This file is the single source of truth for the Celery application definition.

# Load environment variables from a .env file at the project root
# This ensures that REDIS_URL is available when the app is created.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# --- Broker Setup ---
# Use PostgreSQL as the broker and result backend in production
# Fall back to SQLite for local development

database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgresql'):
    # Production: Use PostgreSQL as broker and result backend
    # Broker uses sqla+ prefix, result backend uses db+ prefix
    broker_url = database_url.replace('postgresql://', 'sqla+postgresql://')
    result_backend_url = database_url.replace('postgresql://', 'db+postgresql://')
else:
    # Development: Use SQLite
    # Broker uses sqla+ prefix, result backend uses db+ prefix
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'celery.sqlite3')
    broker_url = f'sqla+sqlite:///{db_path}'
    result_backend_url = f'db+sqlite:///{db_path}'

# Define the Celery application instance.
# The first argument is the name of the project's main module.
# The 'include' argument is a list of modules to import when the worker starts.
app = Celery(
    'tales_tasks',
    broker=broker_url,
    backend=result_backend_url,
    include=['celery_app.tasks']  # This tells Celery to look for tasks in celery_app/tasks.py
)

# Celery configuration settings
app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=3600,

    # Timezone
    timezone='America/New_York',
    enable_utc=True,

    # Production Safety: Task acknowledgment and retry behavior
    # These settings ensure tasks are not lost during worker restarts/deployments
    task_acks_late=True,  # Tasks only acknowledged after completion (not when started)
    task_reject_on_worker_lost=True,  # Re-queue tasks if worker dies unexpectedly
    worker_prefetch_multiplier=1,  # Workers only fetch 1 task at a time (safer, prevents task loss)

    # Task timeouts (for long-running tasks like data collection)
    task_soft_time_limit=600,  # 10 minutes soft limit (raises exception, allows cleanup)
    task_time_limit=900,  # 15 minutes hard limit (kills task)

    # Worker pool settings
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevents memory leaks)
)

# Celery Beat (Scheduler) Configuration
app.conf.beat_schedule = {
    # Check daily for scheduled tasks that are due to run
    'check-scheduled-tasks-daily': {
        'task': 'celery_app.tasks.check_and_run_scheduled_tasks',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2:00 AM ET
    },
}