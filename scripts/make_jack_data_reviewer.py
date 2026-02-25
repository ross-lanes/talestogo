#!/usr/bin/env python3
"""
Make Jack Berkery a data reviewer.

Run this after deploying the data_reviewer role changes.
"""

import os
import sys
from sqlalchemy import create_engine, text

def make_data_reviewer(database_url: str, email: str):
    """Make a user a data reviewer."""
    print(f"🔧 Making {email} a data reviewer...")
    print(f"📊 Database: {database_url.split('@')[1].split('/')[0]}\n")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Update user to be a data reviewer
        result = conn.execute(text('''
            UPDATE users
            SET is_data_reviewer = TRUE
            WHERE email = :email
            RETURNING id, email, full_name, is_data_reviewer
        '''), {'email': email})
        conn.commit()

        user = result.fetchone()
        if user:
            print(f'✅ Updated user:')
            print(f'   ID: {user[0]}')
            print(f'   Email: {user[1]}')
            print(f'   Name: {user[2]}')
            print(f'   Data Reviewer: {user[3]}')
        else:
            print(f'❌ User not found: {email}')
            return False

    print("\n✅ Complete!")
    return True

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Make a user a data reviewer')
    parser.add_argument('--email', type=str, help='User email', default='jberkery@pppl.gov')
    parser.add_argument('--prod', action='store_true', help='Run on PRODUCTION database')
    args = parser.parse_args()

    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL environment variable is not set")
        return 1

    if args.prod:
        confirm = input(f"⚠️  WARNING: This will modify PRODUCTION database. Make {args.email} a data reviewer? Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("❌ Aborted")
            return 1

    try:
        success = make_data_reviewer(db_url, args.email)
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
