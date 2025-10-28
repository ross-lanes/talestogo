"""
Script to delete all responses except the first 88 (by ID).
"""
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "tales.db"

def keep_first_88_responses():
    """Delete all responses except the first 88 by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get total count before deletion
        cursor.execute("SELECT COUNT(*) FROM responses")
        total_before = cursor.fetchone()[0]
        print(f"Total responses before deletion: {total_before}")

        # Get the ID of the 88th response (ordered by ID ascending)
        cursor.execute("""
            SELECT id FROM responses
            ORDER BY id ASC
            LIMIT 1 OFFSET 87
        """)
        result = cursor.fetchone()

        if result is None:
            print("Less than 88 responses exist. No deletion needed.")
            conn.close()
            return

        cutoff_id = result[0]
        print(f"Cutoff ID (88th response): {cutoff_id}")

        # Delete all responses with ID greater than the 88th
        cursor.execute("DELETE FROM responses WHERE id > ?", (cutoff_id,))
        deleted_count = cursor.rowcount

        conn.commit()

        # Get total count after deletion
        cursor.execute("SELECT COUNT(*) FROM responses")
        total_after = cursor.fetchone()[0]

        print(f"Deleted {deleted_count} responses")
        print(f"Total responses after deletion: {total_after}")
        print("✓ Successfully retained first 88 responses")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    keep_first_88_responses()
