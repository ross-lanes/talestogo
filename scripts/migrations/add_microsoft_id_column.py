"""
Database migration script to add microsoft_id column to users table.
Run this script to update the database schema for Microsoft OAuth support.
"""
from dotenv import load_dotenv
load_dotenv(override=True)

import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    exit(1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='users' AND column_name='microsoft_id'
        """))

        if result.fetchone():
            print("✓ Column 'microsoft_id' already exists in users table")
        else:
            print("Adding 'microsoft_id' column to users table...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN microsoft_id VARCHAR(255) UNIQUE
            """))
            conn.commit()

            # Create index
            print("Creating index on microsoft_id...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_users_microsoft_id
                ON users(microsoft_id)
            """))
            conn.commit()

            print("✓ Successfully added microsoft_id column and index")

        # Verify the column was added
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name='users' AND column_name='microsoft_id'
        """))

        row = result.fetchone()
        if row:
            print(f"\nColumn details:")
            print(f"  Name: {row[0]}")
            print(f"  Type: {row[1]}")
            print(f"  Nullable: {row[2]}")
            print("\n✓ Migration completed successfully!")
        else:
            print("\n✗ ERROR: Column was not created")

except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
    print("\nPlease check your database connection and try again.")
    exit(1)
