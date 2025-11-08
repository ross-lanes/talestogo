"""
Fix the PostgreSQL sequence for the users table.
This script resets the sequence to the correct value based on existing data.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url = os.getenv('DATABASE_URL')

if not database_url:
    print("ERROR: DATABASE_URL not found in environment variables")
    exit(1)

print(f"Connecting to database...")

try:
    # Create engine
    engine = create_engine(database_url)

    # Connect and fix the sequence
    with engine.connect() as conn:
        # Get the current max ID
        result = conn.execute(text("SELECT MAX(id) FROM users"))
        max_id = result.scalar()
        print(f"Current max user ID: {max_id}")

        # Reset the sequence to max_id with is_called=true,
        # so next value will be max_id + 1
        conn.execute(text(f"SELECT setval(pg_get_serial_sequence('users', 'id'), {max_id}, true)"))
        conn.commit()

        # Verify the sequence is set correctly
        result = conn.execute(text("SELECT last_value FROM users_id_seq"))
        new_value = result.scalar()
        print(f"Sequence current value: {new_value}")
        print(f"Next user ID will be: {new_value + 1}")
        print("✓ Database sequence fixed successfully!")

except Exception as e:
    print(f"ERROR: Failed to fix sequence: {e}")
    exit(1)
