#!/usr/bin/env python3
"""
Migration: Add tenant support to Tales

This migration:
1. Creates a tenants table
2. Adds tenant_id to users and brand_info tables
3. Creates a default "Generic Tales" tenant
4. Assigns all existing users/brands to the default tenant
"""

import sys
import os
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """Run the tenant migration"""

    with engine.connect() as conn:
        print("Starting tenant migration...")
        print()

        # Step 1: Create tenants table
        print("1. Creating tenants table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tenants (
                id SERIAL PRIMARY KEY,
                tenant_name VARCHAR(200) NOT NULL,
                subdomain VARCHAR(100) UNIQUE,
                logo_url TEXT,
                primary_color VARCHAR(7) DEFAULT '#75C9C8',
                secondary_color VARCHAR(7) DEFAULT '#665775',
                custom_domain VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ Tenants table created")
        print()

        # Step 2: Create default tenant
        print("2. Creating default 'Generic Tales' tenant...")
        result = conn.execute(text("""
            INSERT INTO tenants (tenant_name, subdomain, logo_url, primary_color, secondary_color)
            VALUES ('Generic Tales', NULL, NULL, '#75C9C8', '#665775')
            ON CONFLICT (subdomain) DO NOTHING
            RETURNING id
        """))
        conn.commit()

        default_tenant = conn.execute(text("SELECT id FROM tenants WHERE tenant_name = 'Generic Tales'")).fetchone()
        default_tenant_id = default_tenant[0]
        print(f"   ✓ Default tenant created with ID: {default_tenant_id}")
        print()

        # Step 3: Add tenant_id to users table
        print("3. Adding tenant_id to users table...")
        try:
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id)
            """))
            conn.commit()
            print("   ✓ Added tenant_id column to users")
        except Exception as e:
            print(f"   ⚠ Column may already exist: {e}")
        print()

        # Step 4: Assign all existing users to default tenant
        print("4. Assigning existing users to default tenant...")
        result = conn.execute(text(f"""
            UPDATE users
            SET tenant_id = {default_tenant_id}
            WHERE tenant_id IS NULL
        """))
        conn.commit()
        updated_users = result.rowcount
        print(f"   ✓ Updated {updated_users} users")
        print()

        # Step 5: Add tenant_id to brand_info table
        print("5. Adding tenant_id to brand_info table...")
        try:
            conn.execute(text("""
                ALTER TABLE brand_info
                ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id)
            """))
            conn.commit()
            print("   ✓ Added tenant_id column to brand_info")
        except Exception as e:
            print(f"   ⚠ Column may already exist: {e}")
        print()

        # Step 6: Assign all existing brands to default tenant
        print("6. Assigning existing brands to default tenant...")
        result = conn.execute(text(f"""
            UPDATE brand_info
            SET tenant_id = {default_tenant_id}
            WHERE tenant_id IS NULL
        """))
        conn.commit()
        updated_brands = result.rowcount
        print(f"   ✓ Updated {updated_brands} brands")
        print()

        # Step 7: Add indexes for performance
        print("7. Adding indexes...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_brand_info_tenant_id ON brand_info(tenant_id)
        """))
        conn.commit()
        print("   ✓ Indexes created")
        print()

        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  - Default tenant created: 'Generic Tales' (ID: {default_tenant_id})")
        print(f"  - Users migrated: {updated_users}")
        print(f"  - Brands migrated: {updated_brands}")
        print()
        print("Next steps:")
        print("  1. Update backend models to include tenant_id")
        print("  2. Update API endpoints to filter by tenant")
        print("  3. Add tenant info to authentication response")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
