import os
from celery import Celery
from dotenv import load_dotenv
from celery.schedules import crontab

# --- Celery Application Setup ---
# This file is the single source of truth for the Celery application definition.

# Load environment variables from a .env file at the project root
# This ensures that REDIS_URL is available when the app is created.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# --- SQLite Broker Setup (No External Service Needed) ---
# We will use SQLite as the message broker and result backend.
# This is simple, requires no extra services, and is the modern replacement
# for the old filesystem broker, perfect for development.

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

# Optional Celery configuration settings
app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/New_York',
    enable_utc=True,
)

# Celery Beat (Scheduler) Configuration
app.conf.beat_schedule = {
    # Executes every Friday at 10:00 a.m. ET
    'run-weekly-queries-every-friday-morning': {
        'task': 'celery_app.tasks.run_weekly_queries_task',
        'schedule': crontab(hour=10, minute=0, day_of_week='friday'),
    },
}