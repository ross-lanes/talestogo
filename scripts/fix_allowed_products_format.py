#!/usr/bin/env python3
"""
Fix allowed_products format in database.

Some users have malformed allowed_products values like "{nstxview}" or "{nstxview},nstxview"
instead of clean comma-separated strings like "nstxview" or "tales,heads".

This script:
1. Finds all users with malformed allowed_products
2. Cleans them up to proper format
3. Reports changes made
"""

import os
import sys
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import get_db
from app import models

def clean_allowed_products(value: str) -> str:
    """
    Clean up allowed_products value.

    Examples:
        "{nstxview}" -> "nstxview"
        "{nstxview},nstxview" -> "nstxview"
        "tales,{heads}" -> "tales,heads"
        "tales,heads" -> "tales,heads" (no change)
    """
    if not value:
        return value

    # Remove curly braces
    cleaned = value.replace('{', '').replace('}', '')

    # Split by comma, strip whitespace, remove duplicates, rejoin
    products = [p.strip() for p in cleaned.split(',')]
    products = list(dict.fromkeys(products))  # Remove duplicates while preserving order

    return ','.join(products)

def main():
    print("🔧 Fixing allowed_products format in database...\n")

    # Get database connection
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not set")
        return 1

    print(f"📊 Connecting to database...")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Find all users with allowed_products
        users = db.query(models.User).filter(models.User.allowed_products.isnot(None)).all()

        print(f"Found {len(users)} users with allowed_products set\n")

        fixed_count = 0

        for user in users:
            original = user.allowed_products
            cleaned = clean_allowed_products(original)

            if original != cleaned:
                print(f"👤 {user.email}")
                print(f"   Before: {repr(original)}")
                print(f"   After:  {repr(cleaned)}")

                user.allowed_products = cleaned
                fixed_count += 1

        if fixed_count > 0:
            print(f"\n💾 Committing {fixed_count} change(s) to database...")
            db.commit()
            print("✅ Changes committed successfully!")
        else:
            print("✅ No changes needed - all allowed_products are properly formatted!")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        return 1

    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())
