"""
Migration: Add allowed_products column to users table

This migration adds user-level app access control.

Default rules:
- robotrachel@gmail.com -> tales,heads,canon (full access)
- *@solsticehc.net -> tales,heads,canon (full access)
- Everyone else -> tales (default)

Usage:
    # For development database:
    DATABASE_URL="postgresql://..." python -m migrations.add_allowed_products

    # Or set the environment variable first:
    export DATABASE_URL="postgresql://..."
    python -m migrations.add_allowed_products
"""

import os
import sys
from sqlalchemy import create_engine, text

def get_database_url():
    """Get database URL from environment variable."""
    # Try multiple possible environment variable names
    url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PUBLIC_URL')

    if not url:
        print("ERROR: No database URL found!")
        print("")
        print("Please set the DATABASE_URL environment variable.")
        print("")
        print("For Railway, you can get this from:")
        print("  1. Go to Railway dashboard")
        print("  2. Click on your Postgres database")
        print("  3. Go to 'Variables' tab")
        print("  4. Copy DATABASE_PUBLIC_URL (use PUBLIC for running from local machine)")
        print("")
        print("Then run:")
        print('  DATABASE_URL="your_url_here" python -m migrations.add_allowed_products')
        sys.exit(1)

    return url

def run_migration():
    """Add allowed_products column and set default values."""
    database_url = get_database_url()

    # Mask password in URL for display
    display_url = database_url
    if '@' in display_url:
        parts = display_url.split('@')
        if ':' in parts[0]:
            creds = parts[0].rsplit(':', 1)
            display_url = f"{creds[0]}:****@{parts[1]}"

    print(f"Connecting to database: {display_url}")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'allowed_products'
        """))

        if result.fetchone():
            print("Column 'allowed_products' already exists. Checking data...")
        else:
            print("Adding 'allowed_products' column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN allowed_products TEXT"))
            conn.commit()
            print("Column added successfully!")

        # Count users before update
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        total_users = result.scalar()
        print(f"Total users in database: {total_users}")

        # Update users with full access (robotrachel@gmail.com and @solsticehc.net)
        print("\nSetting full access (tales,heads,canon) for:")
        print("  - robotrachel@gmail.com")
        print("  - *@solsticehc.net")

        result = conn.execute(text("""
            UPDATE users
            SET allowed_products = 'tales,heads,canon'
            WHERE email = 'robotrachel@gmail.com'
               OR email LIKE '%@solsticehc.net'
        """))
        conn.commit()
        full_access_count = result.rowcount
        print(f"  Updated {full_access_count} users with full access")

        # Update remaining users with default access (tales only)
        print("\nSetting default access (tales) for all other users...")
        result = conn.execute(text("""
            UPDATE users
            SET allowed_products = 'tales'
            WHERE allowed_products IS NULL
        """))
        conn.commit()
        default_access_count = result.rowcount
        print(f"  Updated {default_access_count} users with default access")

        # Show summary
        print("\n" + "="*50)
        print("MIGRATION COMPLETE!")
        print("="*50)

        # List users and their access
        result = conn.execute(text("""
            SELECT email, allowed_products
            FROM users
            ORDER BY
                CASE WHEN allowed_products = 'tales,heads,canon' THEN 0 ELSE 1 END,
                email
        """))

        print("\nUser access summary:")
        print("-" * 50)
        for row in result:
            access = row[1] or 'tales'
            products = access.split(',')
            print(f"  {row[0]}: {', '.join(products)}")


if __name__ == "__main__":
    run_migration()
