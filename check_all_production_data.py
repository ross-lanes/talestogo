"""
Check all brands and batches in production database
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Production database URL
PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print(f"\n{'='*80}")
    print(f"PRODUCTION DATABASE - All Brands")
    print(f"{'='*80}\n")

    # List all brands
    brands_result = db.execute(text("""
        SELECT id, brand_name, user_id
        FROM brand_info
        ORDER BY id
    """))

    brands = brands_result.fetchall()

    if brands:
        print(f"Found {len(brands)} brand(s):\n")
        for brand in brands:
            print(f"Brand ID {brand[0]}: {brand[1]} (User ID: {brand[2]})")
    else:
        print("No brands found in production database")

    print(f"\n{'='*80}")
    print(f"PRODUCTION DATABASE - All Collection Batches")
    print(f"{'='*80}\n")

    # List all batches
    batches_result = db.execute(text("""
        SELECT
            cb.id,
            cb.batch_name,
            cb.brand_id,
            cb.user_id,
            bi.brand_name,
            cb.started_at AT TIME ZONE 'UTC' as started_at_utc,
            cb.total_responses,
            cb.status
        FROM collection_batches cb
        LEFT JOIN brand_info bi ON cb.brand_id = bi.id
        ORDER BY cb.started_at DESC
    """))

    batches = batches_result.fetchall()

    if batches:
        print(f"Found {len(batches)} batch(es):\n")
        for batch in batches:
            print(f"Batch ID {batch[0]}: {batch[1]}")
            print(f"  Brand: {batch[4]} (ID: {batch[2]})")
            print(f"  User ID: {batch[3]}")
            print(f"  Started (UTC): {batch[5]}")
            print(f"  Total Responses: {batch[6]}")
            print(f"  Status: {batch[7]}")
            print()
    else:
        print("No batches found in production database")

    print(f"{'='*80}\n")

finally:
    db.close()
