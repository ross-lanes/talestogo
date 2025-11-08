"""Debug script to check leadership visibility calculation"""
import os
os.environ['DATABASE_URL'] = 'postgresql://localhost/tales_db'

from app.database import SessionLocal
from app import models
from app.services import metrics

db = SessionLocal()

# Get all responses for brand_id=1
all_responses = db.query(models.Response).filter(models.Response.brand_id == 1).all()
print(f"Total responses for brand 1: {len(all_responses)}")

# Get all queries for brand_id=1
all_queries = db.query(models.Query).filter(models.Query.brand_id == 1).all()
print(f"Total queries for brand 1: {len(all_queries)}")

# Check how many queries have brand_in_query=True
branded_queries = [q for q in all_queries if q.brand_in_query]
print(f"Queries with brand_in_query=True: {len(branded_queries)}")
print(f"Branded query_ids: {[q.query_id for q in branded_queries]}")

# Check responses from branded queries
branded_query_ids = {q.query_id for q in all_queries if q.brand_in_query}
responses_from_branded_queries = [r for r in all_responses if r.query_id in branded_query_ids]
print(f"\nResponses from branded queries: {len(responses_from_branded_queries)}")

# Check responses NOT from branded queries
responses_not_branded = [r for r in all_responses if r.query_id not in branded_query_ids]
print(f"Responses NOT from branded queries: {len(responses_not_branded)}")

# Check leadership positions in non-branded responses
leadership_positions = ['Leader', 'Top 3', 'Featured']
leadership_in_non_branded = [r for r in responses_not_branded if r.brand_position in leadership_positions]
print(f"\nLeadership positions (Leader/Top 3/Featured) in non-branded responses: {len(leadership_in_non_branded)}")
for r in leadership_in_non_branded[:5]:
    print(f"  - query_id: {r.query_id}, position: {r.brand_position}")

# Calculate using centralized function
lv = metrics.calculate_leadership_visibility(all_responses, all_queries)
print(f"\nLeadership Visibility from centralized function: {lv}%")
print(f"Expected: {len(leadership_in_non_branded)} / {len(responses_not_branded)} * 100 = {(len(leadership_in_non_branded) / len(responses_not_branded) * 100) if len(responses_not_branded) > 0 else 0}%")

db.close()
