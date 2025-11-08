"""
Migrate TALES brand data from localhost to Render database.
This script will:
1. Create the TALES brand in Render (if it doesn't exist)
2. Migrate queries, descriptors, and competitors
3. Migrate responses and collection batches
4. Compute batch analytics for the migrated data
"""
import psycopg2
from datetime import datetime
import json

# Database connections
LOCALHOST_DB = "postgresql://localhost/tales_db"
RENDER_DB = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.ohio-postgres.render.com/tales_3bh3"

# User ID for robotrachel@gmail.com in Render
RENDER_USER_ID = 2

# TALES brand in localhost
LOCALHOST_BRAND_ID = 3
LOCALHOST_USER_ID = 2

def migrate_tales_brand():
    """Migrate TALES brand from localhost to Render."""

    # Connect to both databases
    local_conn = psycopg2.connect(LOCALHOST_DB)
    render_conn = psycopg2.connect(RENDER_DB)

    local_cur = local_conn.cursor()
    render_cur = render_conn.cursor()

    try:
        print("=" * 60)
        print("TALES Brand Migration - Localhost to Render")
        print("=" * 60)

        # Step 1: Get or create TALES brand in Render
        print("\n[1/6] Checking for TALES brand in Render...")
        render_cur.execute(
            "SELECT id FROM brand_info WHERE user_id = %s AND brand_name = 'TALES';",
            (RENDER_USER_ID,)
        )
        result = render_cur.fetchone()

        if result:
            render_brand_id = result[0]
            print(f"   ✓ TALES brand already exists (id={render_brand_id})")
        else:
            # Get brand info from localhost
            local_cur.execute(
                "SELECT brand_name FROM brand_info WHERE id = %s;",
                (LOCALHOST_BRAND_ID,)
            )
            brand_info = local_cur.fetchone()

            # Create brand in Render
            render_cur.execute(
                """INSERT INTO brand_info (user_id, brand_name, is_active, created_at)
                   VALUES (%s, %s, %s, %s) RETURNING id;""",
                (RENDER_USER_ID, brand_info[0], True, datetime.utcnow())
            )
            render_brand_id = render_cur.fetchone()[0]
            render_conn.commit()
            print(f"   ✓ Created TALES brand (id={render_brand_id})")

        # Step 2: Migrate queries
        print("\n[2/6] Migrating queries...")
        local_cur.execute(
            "SELECT query_id, query_text, active, brand_in_query FROM queries WHERE brand_id = %s AND user_id = %s;",
            (LOCALHOST_BRAND_ID, LOCALHOST_USER_ID)
        )
        queries = local_cur.fetchall()

        for query in queries:
            # Check if query already exists
            render_cur.execute(
                "SELECT query_id FROM queries WHERE query_id = %s AND brand_id = %s AND user_id = %s;",
                (query[0], render_brand_id, RENDER_USER_ID)
            )
            if not render_cur.fetchone():
                render_cur.execute(
                    """INSERT INTO queries (query_id, query_text, active, brand_in_query, brand_id, user_id)
                       VALUES (%s, %s, %s, %s, %s, %s);""",
                    (query[0], query[1], query[2], query[3], render_brand_id, RENDER_USER_ID)
                )
        render_conn.commit()
        print(f"   ✓ Migrated {len(queries)} queries")

        # Step 3: Migrate descriptors
        print("\n[3/6] Migrating descriptors...")
        local_cur.execute(
            "SELECT descriptor, is_target, current_ownership, priority, notes FROM target_descriptors WHERE brand_id = %s AND user_id = %s;",
            (LOCALHOST_BRAND_ID, LOCALHOST_USER_ID)
        )
        descriptors = local_cur.fetchall()

        for descriptor in descriptors:
            descriptor_text, is_target, current_ownership, priority, notes = descriptor
            # Check if descriptor already exists
            render_cur.execute(
                "SELECT id FROM target_descriptors WHERE descriptor = %s AND brand_id = %s AND user_id = %s;",
                (descriptor_text, render_brand_id, RENDER_USER_ID)
            )
            if not render_cur.fetchone():
                render_cur.execute(
                    """INSERT INTO target_descriptors (descriptor, is_target, current_ownership, priority, notes, brand_id, user_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s);""",
                    (descriptor_text, is_target, current_ownership, priority, notes, render_brand_id, RENDER_USER_ID)
                )
        render_conn.commit()
        print(f"   ✓ Migrated {len(descriptors)} descriptors")

        # Step 4: Migrate competitors
        print("\n[4/6] Migrating competitors...")
        local_cur.execute(
            "SELECT organization, type, focus_area, track, key_descriptors, website, notes FROM competitors WHERE brand_id = %s AND user_id = %s;",
            (LOCALHOST_BRAND_ID, LOCALHOST_USER_ID)
        )
        competitors = local_cur.fetchall()

        for competitor in competitors:
            organization, comp_type, focus_area, track, key_descriptors, website, notes = competitor
            # Check if competitor already exists
            render_cur.execute(
                "SELECT id FROM competitors WHERE organization = %s AND brand_id = %s AND user_id = %s;",
                (organization, render_brand_id, RENDER_USER_ID)
            )
            if not render_cur.fetchone():
                render_cur.execute(
                    """INSERT INTO competitors (organization, type, focus_area, track, key_descriptors, website, notes, brand_id, user_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                    (organization, comp_type, focus_area, track, key_descriptors, website, notes, render_brand_id, RENDER_USER_ID)
                )
        render_conn.commit()
        print(f"   ✓ Migrated {len(competitors)} competitors")

        # Step 5: Migrate collection batches
        print("\n[5/6] Migrating collection batches...")
        local_cur.execute(
            """SELECT id, started_at, completed_at, status, total_queries, total_responses, created_at
               FROM collection_batches WHERE brand_id = %s AND user_id = %s ORDER BY started_at;""",
            (LOCALHOST_BRAND_ID, LOCALHOST_USER_ID)
        )
        batches = local_cur.fetchall()

        batch_id_map = {}  # Map localhost batch_id to render batch_id

        for batch in batches:
            local_batch_id = batch[0]
            # Check if batch already exists (by started_at timestamp)
            render_cur.execute(
                "SELECT id FROM collection_batches WHERE brand_id = %s AND user_id = %s AND started_at = %s;",
                (render_brand_id, RENDER_USER_ID, batch[1])
            )
            result = render_cur.fetchone()

            if result:
                render_batch_id = result[0]
            else:
                # Generate a batch name based on the date
                batch_name = f"TALES {batch[1].strftime('%Y-%m-%d %H:%M')}"
                render_cur.execute(
                    """INSERT INTO collection_batches
                       (started_at, completed_at, status, total_queries, total_responses, created_at, brand_id, user_id, batch_name)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;""",
                    (batch[1], batch[2], batch[3], batch[4], batch[5], batch[6], render_brand_id, RENDER_USER_ID, batch_name)
                )
                render_batch_id = render_cur.fetchone()[0]

            batch_id_map[local_batch_id] = render_batch_id

        render_conn.commit()
        print(f"   ✓ Migrated {len(batches)} collection batches")

        # Step 6: Migrate responses
        print("\n[6/6] Migrating responses...")
        local_cur.execute(
            """SELECT query_id, query_text, platform, response_text, brand_mentioned, brand_position, sentiment,
                      competitors, descriptors, sources, timestamp, batch_id, analyzed_at, notes
               FROM responses WHERE brand_id = %s AND user_id = %s;""",
            (LOCALHOST_BRAND_ID, LOCALHOST_USER_ID)
        )
        responses = local_cur.fetchall()

        migrated_count = 0
        for response in responses:
            query_id, query_text, platform, response_text, brand_mentioned, brand_position, sentiment, \
                competitors_str, descriptors_str, sources, timestamp, local_batch_id, analyzed_at, notes = response

            # Map to render batch_id
            render_batch_id = batch_id_map.get(local_batch_id)

            # Check if response already exists
            render_cur.execute(
                """SELECT id FROM responses
                   WHERE query_id = %s AND platform = %s AND brand_id = %s AND user_id = %s AND batch_id = %s;""",
                (query_id, platform, render_brand_id, RENDER_USER_ID, render_batch_id)
            )

            if not render_cur.fetchone():
                render_cur.execute(
                    """INSERT INTO responses
                       (query_id, query_text, platform, response_text, brand_mentioned, brand_position, sentiment,
                        competitors, descriptors, sources, timestamp, batch_id, brand_id, user_id, analyzed_at, notes)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                    (query_id, query_text, platform, response_text, brand_mentioned, brand_position, sentiment,
                     competitors_str, descriptors_str, sources, timestamp, render_batch_id, render_brand_id,
                     RENDER_USER_ID, analyzed_at, notes)
                )
                migrated_count += 1

        render_conn.commit()
        print(f"   ✓ Migrated {migrated_count} responses (skipped {len(responses) - migrated_count} duplicates)")

        print("\n" + "=" * 60)
        print("Migration Complete!")
        print("=" * 60)
        print(f"\nTALES brand migrated successfully:")
        print(f"  Render Brand ID: {render_brand_id}")
        print(f"  Queries: {len(queries)}")
        print(f"  Descriptors: {len(descriptors)}")
        print(f"  Competitors: {len(competitors)}")
        print(f"  Batches: {len(batches)}")
        print(f"  Responses: {migrated_count}")
        print("\nNext step: Compute batch analytics for the migrated batches")

        return render_brand_id, batch_id_map

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        render_conn.rollback()
        raise
    finally:
        local_cur.close()
        local_conn.close()
        render_cur.close()
        render_conn.close()


if __name__ == "__main__":
    render_brand_id, batch_id_map = migrate_tales_brand()

    # Now compute batch analytics
    print("\nComputing batch analytics for migrated batches...")
    import sys
    sys.path.insert(0, '.')
    from app.database import SessionLocal
    from app.services.batch_analytics import compute_batch_analytics

    db = SessionLocal()
    try:
        for local_batch_id, render_batch_id in batch_id_map.items():
            print(f"  Processing batch {render_batch_id}...")
            analytics = compute_batch_analytics(
                db=db,
                batch_id=render_batch_id,
                user_id=RENDER_USER_ID,
                brand_id=render_brand_id
            )
            if analytics:
                print(f"    ✓ Analytics computed (mention_rate={analytics.mention_rate}%)")
            else:
                print(f"    ⚠ No analytics (no responses)")
        db.commit()
        print("\n✅ All batch analytics computed successfully!")
    except Exception as e:
        print(f"\n❌ Error computing analytics: {e}")
        db.rollback()
    finally:
        db.close()
