"""
Migration script to assign existing users to RobotRachel tenant.

This script:
1. Creates the "RobotRachel" tenant if it doesn't exist
2. Assigns all users with tenant_id=None to the RobotRachel tenant
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
    """Assign all users without a tenant to RobotRachel tenant."""
    db = SessionLocal()

    try:
        # Create or get RobotRachel tenant
        tenant = db.query(models.Tenant).filter(
            models.Tenant.tenant_name == 'RobotRachel'
        ).first()

        if not tenant:
            print("Creating 'RobotRachel' tenant...")
            tenant = models.Tenant(
                tenant_name='RobotRachel',
                primary_color='#75C9C8',
                secondary_color='#665775'
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"✓ Created 'RobotRachel' tenant (ID: {tenant.id})")
        else:
            print(f"✓ Found existing 'RobotRachel' tenant (ID: {tenant.id})")

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

        # Assign them to RobotRachel tenant
        print(f"\nAssigning users to 'RobotRachel' tenant...")
        for user in users_without_tenant:
            user.tenant_id = tenant.id
            print(f"  ✓ {user.email} → RobotRachel")

        db.commit()
        print(f"\n✓ Successfully assigned {len(users_without_tenant)} user(s) to RobotRachel tenant!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Assigning Existing Users to RobotRachel Tenant")
    print("=" * 60)
    print()

    assign_users_to_generic_tenant()

    print()
    print("=" * 60)
    print("Migration Complete!")
    print("=" * 60)
