"""
Run rollback migration on Railway database from local machine

This script connects to the Railway database using the DATABASE_URL
and runs the rollback migration to remove pending shares columns.

Usage:
    railway run python migrations/run_rollback_on_railway.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_rollback():
    """Run the rollback SQL commands"""

    # Import after path is set
    from sqlalchemy import create_engine, text

    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not found")
        print("This script must be run with: railway run python migrations/run_rollback_on_railway.py")
        sys.exit(1)

    print("=" * 60)
    print("DATABASE ROLLBACK: Remove Pending Shares Feature")
    print("=" * 60)
    print()
    print(f"Connected to database: {database_url[:30]}...")
    print()

    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            print("Step 1: Checking for pending shares...")
            result = conn.execute(text("SELECT COUNT(*) FROM brand_shares WHERE user_id IS NULL"))
            count = result.scalar()
            print(f"  Found {count} pending share(s) to delete")

            if count > 0:
                conn.execute(text("DELETE FROM brand_shares WHERE user_id IS NULL"))
                print(f"  ✓ Deleted {count} pending share(s)")

            print("\nStep 2: Making user_id NOT NULL...")
            conn.execute(text("ALTER TABLE brand_shares ALTER COLUMN user_id SET NOT NULL"))
            print("  ✓ user_id is now NOT NULL")

            print("\nStep 3: Dropping indexes...")
            conn.execute(text("DROP INDEX IF EXISTS ix_brand_shares_pending_email"))
            conn.execute(text("DROP INDEX IF EXISTS ix_brand_shares_is_pending"))
            print("  ✓ Indexes dropped")

            print("\nStep 4: Dropping columns...")
            conn.execute(text("ALTER TABLE brand_shares DROP COLUMN IF EXISTS pending_email"))
            conn.execute(text("ALTER TABLE brand_shares DROP COLUMN IF EXISTS is_pending"))
            print("  ✓ Columns dropped")

            conn.commit()

            print("\n" + "=" * 60)
            print("✅ Rollback completed successfully!")
            print("=" * 60)
            print()
            print("The brand_shares table has been restored to its original schema.")
            print("You can now share brands with existing users.")

    except Exception as e:
        print(f"\n❌ Rollback failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run_rollback()
