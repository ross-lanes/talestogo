#!/usr/bin/env python3
"""
Comprehensive Migration Runner
Runs all necessary database migrations in the correct order to fix production login issues.

This script will:
1. Create tenants table if it doesn't exist
2. Add tenant_id column to users table if missing
3. Create RobotRachel tenant
4. Assign all users to RobotRachel tenant
5. Activate all users (set is_active=True)
6. Set OAuth providers based on email domain

Usage:
    python migrations/run_all_migrations.py
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal, engine
from app.models import User, Tenant
from app.auth import get_oauth_provider_for_email


def step1_create_tenants_table():
    """Step 1: Create tenants table if it doesn't exist"""
    print("\n" + "="*60)
    print("STEP 1: Creating Tenants Table")
    print("="*60)

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id SERIAL PRIMARY KEY,
                    tenant_name VARCHAR(200) NOT NULL UNIQUE,
                    subdomain VARCHAR(100),
                    logo_url VARCHAR(500),
                    primary_color VARCHAR(20) DEFAULT '#75C9C8',
                    secondary_color VARCHAR(20) DEFAULT '#665775',
                    custom_domain VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            trans.commit()
            print("✓ Tenants table created/verified")
            return True
        except Exception as e:
            trans.rollback()
            print(f"✗ Error: {e}")
            return False


def step2_add_tenant_column():
    """Step 2: Add tenant_id column to users table if missing"""
    print("\n" + "="*60)
    print("STEP 2: Adding tenant_id Column to Users Table")
    print("="*60)

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='tenant_id'
            """))

            if result.fetchone():
                print("✓ tenant_id column already exists")
            else:
                print("Adding tenant_id column...")
                conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)
                """))
                print("✓ tenant_id column added")

            # Create index
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id)
            """))
            print("✓ Index created")

            trans.commit()
            return True
        except Exception as e:
            trans.rollback()
            print(f"✗ Error: {e}")
            return False


def step3_create_robotrachel_tenant():
    """Step 3: Create RobotRachel tenant"""
    print("\n" + "="*60)
    print("STEP 3: Creating RobotRachel Tenant")
    print("="*60)

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(
            Tenant.tenant_name == 'RobotRachel'
        ).first()

        if tenant:
            print(f"✓ RobotRachel tenant already exists (ID: {tenant.id})")
        else:
            tenant = Tenant(
                tenant_name='RobotRachel',
                primary_color='#75C9C8',
                secondary_color='#665775'
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"✓ Created RobotRachel tenant (ID: {tenant.id})")

        return True
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        return False
    finally:
        db.close()


def step4_assign_users_and_activate():
    """Step 4: Assign users to tenant, activate them, and set OAuth providers"""
    print("\n" + "="*60)
    print("STEP 4: Assigning Users to Tenant & Activating")
    print("="*60)

    db = SessionLocal()
    try:
        # Get RobotRachel tenant
        tenant = db.query(Tenant).filter(
            Tenant.tenant_name == 'RobotRachel'
        ).first()

        if not tenant:
            print("✗ RobotRachel tenant not found!")
            return False

        # Get all users
        users = db.query(User).all()
        print(f"\nFound {len(users)} user(s):")

        updated_count = 0
        activated_count = 0
        oauth_updated_count = 0
        assigned_count = 0

        for user in users:
            changes = []

            # Assign to tenant if not assigned
            if user.tenant_id is None:
                user.tenant_id = tenant.id
                assigned_count += 1
                changes.append(f'assigned to tenant')

            # Activate user
            if not user.is_active:
                user.is_active = True
                activated_count += 1
                changes.append('activated')

            # Set OAuth provider based on email domain
            if not user.oauth_provider:
                oauth_provider = get_oauth_provider_for_email(user.email)
                if oauth_provider:
                    user.oauth_provider = oauth_provider
                    oauth_updated_count += 1
                    changes.append(f'oauth={oauth_provider}')

            if changes:
                updated_count += 1
                print(f"  ✓ {user.email}: {', '.join(changes)}")
            else:
                print(f"  → {user.email}: already configured")

        db.commit()

        print(f"\n" + "="*60)
        print("Summary:")
        print(f"  Users assigned to tenant: {assigned_count}")
        print(f"  Users activated: {activated_count}")
        print(f"  OAuth providers set: {oauth_updated_count}")
        print(f"  Total users updated: {updated_count}")
        print("="*60)

        return True
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def run_all_migrations():
    """Run all migration steps in order"""
    print("\n" + "="*60)
    print("COMPREHENSIVE MIGRATION RUNNER")
    print("Fixing Production Login Issues")
    print("="*60)

    steps = [
        ("Create Tenants Table", step1_create_tenants_table),
        ("Add Tenant Column", step2_add_tenant_column),
        ("Create RobotRachel Tenant", step3_create_robotrachel_tenant),
        ("Assign & Activate Users", step4_assign_users_and_activate),
    ]

    for step_name, step_func in steps:
        success = step_func()
        if not success:
            print(f"\n✗ Migration failed at: {step_name}")
            return False

    print("\n" + "="*60)
    print("🎉 ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nAll users can now login to tales.robotrachel.com!")
    print()

    return True


if __name__ == '__main__':
    success = run_all_migrations()
    sys.exit(0 if success else 1)
