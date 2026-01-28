"""
Reset auto-increment sequences for all tables to match current max IDs.

This fixes the "duplicate key value violates unique constraint" error
that occurs when sequences get out of sync with actual data.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def reset_all_sequences(database_url: str = None):
    """
    Reset all auto-increment sequences to match the current max ID in each table.

    This prevents "duplicate key value" errors when inserting new records.
    """
    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment")

    engine = create_engine(db_url)

    # List of tables with auto-increment primary keys
    tables = [
        'users',
        'queries',
        'responses',
        'target_descriptors',
        'competitors',
        'brand_info',
        'brand_shares',
        'task_status',
        'reports'
    ]

    with engine.connect() as conn:
        for table in tables:
            try:
                # Get the sequence name for this table's id column
                result = conn.execute(text(f"""
                    SELECT pg_get_serial_sequence('{table}', 'id')
                """))
                sequence_name = result.scalar()

                if sequence_name:
                    # Reset the sequence to max(id) + 1
                    conn.execute(text(f"""
                        SELECT setval(
                            '{sequence_name}',
                            COALESCE((SELECT MAX(id) FROM {table}), 1),
                            true
                        )
                    """))
                    print(f"✓ Reset sequence for {table}")
                else:
                    print(f"  Skipped {table} (no auto-increment sequence)")
            except Exception as e:
                print(f"  Error resetting {table}: {e}")

        conn.commit()

    print("\n✓ All sequences reset successfully!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reset auto-increment sequences")
    parser.add_argument("--database-url", type=str, help="Database URL (optional)")
    args = parser.parse_args()

    reset_all_sequences(args.database_url)
