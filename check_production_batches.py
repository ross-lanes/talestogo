"""
Quick script to check batches in production database
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Production database URL (from .env line 20)
PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

# Create engine and session
engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Query batches for Physics of Plasmas (brand_id=2, user_id=2)
    result = db.execute(text("""
        SELECT
            id,
            batch_name,
            started_at AT TIME ZONE 'UTC' as started_at_utc,
            started_at AT TIME ZONE 'America/New_York' as started_at_est,
            completed_at AT TIME ZONE 'UTC' as completed_at_utc,
            total_responses,
            status
        FROM collection_batches
        WHERE brand_id = 2 AND user_id = 2
        ORDER BY started_at DESC
    """))

    batches = result.fetchall()

    print(f"\n{'='*80}")
    print(f"PRODUCTION DATABASE - Physics of Plasmas Batches")
    print(f"{'='*80}\n")

    if batches:
        print(f"Found {len(batches)} batch(es):\n")
        for batch in batches:
            print(f"Batch ID: {batch[0]}")
            print(f"  Name: {batch[1]}")
            print(f"  Started (UTC): {batch[2]}")
            print(f"  Started (EST): {batch[3]}")
            print(f"  Completed (UTC): {batch[4]}")
            print(f"  Total Responses: {batch[5]}")
            print(f"  Status: {batch[6]}")
            print()
    else:
        print("No batches found for Physics of Plasmas (brand_id=2, user_id=2)")

    print(f"{'='*80}\n")

finally:
    db.close()
