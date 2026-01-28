"""Debug dashboard calculation step by step"""
import os
os.environ['DATABASE_URL'] = 'postgresql://localhost/tales_db'

from app.database import SessionLocal
from app import models
from sqlalchemy import func, and_

db = SessionLocal()

user_id = 1
brand_id = 1

# Simulate the apply_filters_exclude_brand_in_query function
query = db.query(func.count(models.Response.id)).join(
    models.Query,
    (models.Response.query_id == models.Query.query_id) &
    (models.Response.user_id == models.Query.user_id) &
    (models.Response.brand_id == models.Query.brand_id)
).filter(
    models.Response.user_id == user_id,
    models.Query.brand_in_query == False  # Exclude queries with brand name
)
if brand_id:
    query = query.filter(models.Response.brand_id == brand_id)

total_responses = query.scalar() or 0
print(f"total_responses (from apply_filters_exclude_brand_in_query): {total_responses}")

# Now check without the join
simple_count = db.query(func.count(models.Response.id)).filter(
    models.Response.user_id == user_id,
    models.Response.brand_id == brand_id
).scalar()
print(f"simple count (no join): {simple_count}")

# Check if the join is the problem
join_count = db.query(func.count(models.Response.id)).join(
    models.Query,
    (models.Response.query_id == models.Query.query_id) &
    (models.Response.user_id == models.Query.user_id) &
    (models.Response.brand_id == models.Query.brand_id)
).filter(
    models.Response.user_id == user_id,
    models.Response.brand_id == brand_id
).scalar()
print(f"join count (no brand_in_query filter): {join_count}")

db.close()
