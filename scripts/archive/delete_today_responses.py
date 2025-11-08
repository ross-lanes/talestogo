#!/usr/bin/env python3
"""
Script to delete responses from today's date from the production database.
This is useful for removing incomplete data collections.

Usage:
    python3 delete_today_responses.py --user-id YOUR_USER_ID --brand-id YOUR_BRAND_ID [--dry-run]
"""

import os
import sys
import argparse
import datetime
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Response
from app.database import Base


def delete_today_responses(database_url: str, user_id: int, brand_id: int, dry_run: bool = False):
    """
    Delete all responses from today for the specified user and brand.

    Args:
        database_url: PostgreSQL connection string
        user_id: User ID to filter by
        brand_id: Brand ID to filter by
        dry_run: If True, only show what would be deleted without actually deleting
    """
    # Create database connection
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Get today's date range (from midnight to now)
        today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        now = datetime.datetime.utcnow()

        print(f"\n{'='*60}")
        print(f"DELETE RESPONSES FROM TODAY")
        print(f"{'='*60}")
        print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
        print(f"User ID: {user_id}")
        print(f"Brand ID: {brand_id}")
        print(f"Time Range: {today_start.strftime('%Y-%m-%d %H:%M:%S')} to {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (will delete data)'}")
        print(f"{'='*60}\n")

        # Query for responses from today
        query = db.query(Response).filter(
            and_(
                Response.user_id == user_id,
                Response.brand_id == brand_id,
                Response.timestamp >= today_start,
                Response.timestamp <= now
            )
        )

        # Count total responses
        total_count = query.count()

        if total_count == 0:
            print("✓ No responses found from today. Nothing to delete.")
            return

        # Get breakdown by platform
        platform_counts = {}
        for response in query.all():
            platform = response.platform
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        # Display what will be deleted
        print(f"Found {total_count} responses from today:\n")
        for platform, count in sorted(platform_counts.items()):
            print(f"  • {platform}: {count} responses")

        # Get sample of responses (first 5)
        sample_responses = query.limit(5).all()
        print(f"\nSample responses (showing first 5):")
        for i, resp in enumerate(sample_responses, 1):
            print(f"\n  {i}. Platform: {resp.platform}")
            print(f"     Query: {resp.query_text[:100]}...")
            print(f"     Timestamp: {resp.timestamp}")
            print(f"     Brand Mentioned: {resp.brand_mentioned}")
            print(f"     Position: {resp.brand_position}")

        print(f"\n{'='*60}")

        if dry_run:
            print("\n✓ DRY RUN COMPLETE - No data was deleted")
            print(f"  To actually delete these {total_count} responses, run without --dry-run flag")
        else:
            # Ask for confirmation
            print(f"\n⚠️  WARNING: You are about to DELETE {total_count} responses!")
            print("   This action CANNOT be undone.")
            confirmation = input("\nType 'DELETE' to confirm: ")

            if confirmation != 'DELETE':
                print("\n✗ Deletion cancelled. No data was deleted.")
                return

            # Perform deletion
            deleted_count = query.delete(synchronize_session=False)
            db.commit()

            print(f"\n✓ Successfully deleted {deleted_count} responses from today")
            print(f"  User ID: {user_id}")
            print(f"  Brand ID: {brand_id}")
            print(f"  Date: {today_start.strftime('%Y-%m-%d')}")

    except Exception as e:
        db.rollback()
        print(f"\n✗ ERROR: {str(e)}")
        raise

    finally:
        db.close()
        print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Delete responses from today for a specific user and brand',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (see what would be deleted without deleting):
  python3 delete_today_responses.py --user-id 1 --brand-id 1 --dry-run

  # Actually delete (use production database URL):
  DATABASE_URL="postgresql://user:pass@host/dbname" python3 delete_today_responses.py --user-id 1 --brand-id 1

  # Use local database:
  DATABASE_URL="postgresql://localhost/tales_db" python3 delete_today_responses.py --user-id 1 --brand-id 1
        """
    )

    parser.add_argument('--user-id', type=int, required=True,
                       help='User ID to delete responses for')
    parser.add_argument('--brand-id', type=int, required=True,
                       help='Brand ID to delete responses for')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')

    args = parser.parse_args()

    # Get database URL from environment or use local default
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("\nPlease set it to your production database connection string:")
        print('  export DATABASE_URL="postgresql://user:password@host/database"')
        print("\nOr for local database:")
        print('  export DATABASE_URL="postgresql://localhost/tales_db"')
        sys.exit(1)

    # Run deletion
    delete_today_responses(
        database_url=database_url,
        user_id=args.user_id,
        brand_id=args.brand_id,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    main()
