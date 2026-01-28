"""Check TaskStatus for recent tasks"""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.models import TaskStatus, User, BrandInfo

engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

try:
    # Get tasks from last hour
    cutoff = datetime.utcnow() - timedelta(hours=1)
    tasks = db.query(TaskStatus).filter(
        TaskStatus.started_at >= cutoff
    ).order_by(TaskStatus.started_at.desc()).all()

    print(f"\n{'='*80}")
    print(f"TASK STATUS - Last Hour ({len(tasks)} tasks)")
    print(f"{'='*80}\n")

    for task in tasks:
        user = db.query(User).filter_by(id=task.user_id).first()
        brand = db.query(BrandInfo).filter_by(id=task.brand_id).first()

        print(f"Task ID: {task.id}")
        print(f"  User: {user.email if user else 'Unknown'}")
        print(f"  Brand: {brand.brand_name if brand else 'Unknown'}")
        print(f"  Type: {task.task_type}")
        print(f"  Status: {task.status}")
        print(f"  Started: {task.started_at}")
        print(f"  Message: {task.message}")
        print(f"  Progress: {task.processed_items}/{task.total_items}")
        print()

finally:
    db.close()
