"""
List all users in the database
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User, BrandInfo, Query

def list_all_users():
    """List all users with their basic info"""
    db = SessionLocal()

    try:
        users = db.query(User).all()

        print(f"\n{'='*80}")
        print(f"ALL USERS IN DATABASE ({len(users)} total)")
        print(f"{'='*80}\n")

        if not users:
            print("❌ No users found in database\n")
            return

        for user in users:
            # Get counts
            brands_count = db.query(BrandInfo).filter_by(user_id=user.id).count()
            queries_count = db.query(Query).filter_by(user_id=user.id).count()

            print(f"{'-'*80}")
            print(f"Email:        {user.email}")
            print(f"Name:         {user.full_name if user.full_name else 'Not set'}")
            print(f"Organization: {user.organization if user.organization else 'Not set'}")
            print(f"Active:       {'✅ Yes' if user.is_active else '❌ No'}")
            print(f"Admin:        {'✅ Yes' if user.is_admin else 'No'}")
            print(f"Tenant ID:    {user.tenant_id}")
            print(f"Brands:       {brands_count}")
            print(f"Queries:      {queries_count}")
            print()

    finally:
        db.close()


if __name__ == "__main__":
    list_all_users()
