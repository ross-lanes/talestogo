#!/usr/bin/env python3
"""
Script to delete all responses from the database.
"""
from app.database import SessionLocal
from app.models import Response

def delete_all_responses():
    """Delete all responses from the database."""
    db = SessionLocal()
    try:
        # Get count before deletion
        count = db.query(Response).count()
        print(f"Found {count} responses in the database")

        if count == 0:
            print("No responses to delete")
            return

        # Delete all responses
        db.query(Response).delete()
        db.commit()

        print(f"Successfully deleted all {count} response(s)")

        # Verify deletion
        remaining = db.query(Response).count()
        print(f"Remaining responses: {remaining}")

    except Exception as e:
        db.rollback()
        print(f"Error deleting responses: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_responses()
