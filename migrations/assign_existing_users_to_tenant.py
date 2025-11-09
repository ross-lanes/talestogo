"""
Migration script to assign existing users to Generic Tales tenant.

This script:
1. Creates the "Generic Tales" tenant if it doesn't exist
2. Assigns all users with tenant_id=None to the Generic Tales tenant
3. Reports on how many users were updated

Run this script with:
    python migrations/assign_existing_users_to_tenant.py
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app import models

def assign_users_to_generic_tenant():
    """Assign all users without a tenant to Generic Tales tenant."""
    db = SessionLocal()

    try:
        # Create or get Generic Tales tenant
        tenant = db.query(models.Tenant).filter(
            models.Tenant.tenant_name == 'Generic Tales'
        ).first()

        if not tenant:
            print("Creating 'Generic Tales' tenant...")
            tenant = models.Tenant(
                tenant_name='Generic Tales',
                primary_color='#75C9C8',
                secondary_color='#665775'
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"✓ Created 'Generic Tales' tenant (ID: {tenant.id})")
        else:
            print(f"✓ Found existing 'Generic Tales' tenant (ID: {tenant.id})")

        # Find all users without a tenant
        users_without_tenant = db.query(models.User).filter(
            models.User.tenant_id == None
        ).all()

        if not users_without_tenant:
            print("\n✓ No users without a tenant. All users are already assigned!")
            return

        print(f"\nFound {len(users_without_tenant)} user(s) without a tenant:")
        for user in users_without_tenant:
            print(f"  - {user.email} (ID: {user.id})")

        # Assign them to Generic Tales tenant
        print(f"\nAssigning users to 'Generic Tales' tenant...")
        for user in users_without_tenant:
            user.tenant_id = tenant.id
            print(f"  ✓ {user.email} → Generic Tales")

        db.commit()
        print(f"\n✓ Successfully assigned {len(users_without_tenant)} user(s) to Generic Tales tenant!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Assigning Existing Users to Generic Tales Tenant")
    print("=" * 60)
    print()

    assign_users_to_generic_tenant()

    print()
    print("=" * 60)
    print("Migration Complete!")
    print("=" * 60)
