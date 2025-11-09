#!/usr/bin/env python3
"""
Migration: Add Solstice Health Communications tenant

This migration:
1. Creates a tenant for Solstice Health Communications
2. Sets up their brand colors (#003F62, #F04B25, #C6CECE, #54B6B2)
3. Migrates any existing users with @solsticehc.net to this tenant
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """Run the Solstice tenant migration"""

    with engine.connect() as conn:
        print("Starting Solstice Health Communications tenant migration...")
        print()

        # Step 1: Check if Solstice tenant already exists
        print("1. Checking for existing Solstice tenant...")
        result = conn.execute(text("""
            SELECT id FROM tenants WHERE tenant_name = 'Solstice Health Communications'
        """))
        existing_tenant = result.fetchone()

        if existing_tenant:
            solstice_tenant_id = existing_tenant[0]
            print(f"   ⚠ Solstice tenant already exists with ID: {solstice_tenant_id}")
        else:
            # Create Solstice tenant
            print("   Creating Solstice Health Communications tenant...")
            result = conn.execute(text("""
                INSERT INTO tenants (tenant_name, subdomain, primary_color, secondary_color)
                VALUES ('Solstice Health Communications', 'solstice', '#003F62', '#F04B25')
                RETURNING id
            """))
            conn.commit()
            solstice_tenant_id = result.fetchone()[0]
            print(f"   ✓ Solstice tenant created with ID: {solstice_tenant_id}")
        print()

        # Step 2: Migrate users with @solsticehc.net emails
        print("2. Migrating users with @solsticehc.net emails...")
        result = conn.execute(text(f"""
            UPDATE users
            SET tenant_id = {solstice_tenant_id}
            WHERE email LIKE '%@solsticehc.net'
            AND (tenant_id IS NULL OR tenant_id != {solstice_tenant_id})
        """))
        conn.commit()
        updated_users = result.rowcount
        print(f"   ✓ Migrated {updated_users} Solstice users")
        print()

        # Step 3: Migrate brands owned by Solstice users
        print("3. Migrating brands owned by Solstice users...")
        result = conn.execute(text(f"""
            UPDATE brand_info
            SET tenant_id = {solstice_tenant_id}
            WHERE user_id IN (
                SELECT id FROM users WHERE tenant_id = {solstice_tenant_id}
            )
            AND (tenant_id IS NULL OR tenant_id != {solstice_tenant_id})
        """))
        conn.commit()
        updated_brands = result.rowcount
        print(f"   ✓ Migrated {updated_brands} brands")
        print()

        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  - Solstice tenant ID: {solstice_tenant_id}")
        print(f"  - Primary color: #003F62 (Navy)")
        print(f"  - Secondary color: #F04B25 (Orange)")
        print(f"  - Additional colors: #C6CECE (Gray), #54B6B2 (Teal)")
        print(f"  - Users migrated: {updated_users}")
        print(f"  - Brands migrated: {updated_brands}")
        print()
        print("Next steps:")
        print("  1. Update user creation logic to auto-assign Solstice tenant")
        print("  2. Update frontend to apply tenant branding")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
