#!/usr/bin/env python3
"""
Migration: Add admin_audit_logs table for security auditing

This migration:
1. Creates admin_audit_logs table
2. Creates indexes for performance
3. Tracks admin impersonation events and other admin actions
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """Run the admin audit logs migration"""

    with engine.connect() as conn:
        print("Starting admin audit logs migration...")
        print()

        # Step 1: Create admin_audit_logs table
        print("1. Creating admin_audit_logs table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_audit_logs (
                id SERIAL PRIMARY KEY,
                admin_user_id INTEGER NOT NULL REFERENCES users(id),
                action_type VARCHAR(100) NOT NULL,
                target_user_id INTEGER REFERENCES users(id),
                details TEXT,
                ip_address VARCHAR(45),
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("   ✅ admin_audit_logs table created")

        # Step 2: Create indexes
        print("2. Creating indexes...")

        # Index for admin user ID
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_admin_user_id
            ON admin_audit_logs(admin_user_id)
        """))
        print("   ✅ Index on admin_user_id created")

        # Index for action type
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_action_type
            ON admin_audit_logs(action_type)
        """))
        print("   ✅ Index on action_type created")

        # Index for target user ID
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_target_user_id
            ON admin_audit_logs(target_user_id)
        """))
        print("   ✅ Index on target_user_id created")

        # Index for timestamp
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_timestamp
            ON admin_audit_logs(timestamp)
        """))
        print("   ✅ Index on timestamp created")

        # Composite index for admin + action + time queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_admin_action
            ON admin_audit_logs(admin_user_id, action_type, timestamp)
        """))
        print("   ✅ Composite index for admin queries created")

        # Composite index for target user + time queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_target_user
            ON admin_audit_logs(target_user_id, timestamp)
        """))
        print("   ✅ Composite index for target user queries created")

        conn.commit()
        print()
        print("✅ Migration completed successfully!")
        print()
        print("Admin audit logs table is now ready to track:")
        print("  - Admin impersonation events")
        print("  - Future admin actions as needed")


def rollback_migration():
    """Rollback the admin audit logs migration"""

    with engine.connect() as conn:
        print("Rolling back admin audit logs migration...")
        print()

        # Drop indexes first
        print("1. Dropping indexes...")
        conn.execute(text("DROP INDEX IF EXISTS idx_audit_target_user"))
        conn.execute(text("DROP INDEX IF EXISTS idx_audit_admin_action"))
        conn.execute(text("DROP INDEX IF EXISTS ix_admin_audit_logs_timestamp"))
        conn.execute(text("DROP INDEX IF EXISTS ix_admin_audit_logs_target_user_id"))
        conn.execute(text("DROP INDEX IF EXISTS ix_admin_audit_logs_action_type"))
        conn.execute(text("DROP INDEX IF EXISTS ix_admin_audit_logs_admin_user_id"))
        print("   ✅ Indexes dropped")

        # Drop table
        print("2. Dropping admin_audit_logs table...")
        conn.execute(text("DROP TABLE IF EXISTS admin_audit_logs"))
        print("   ✅ Table dropped")

        conn.commit()
        print()
        print("✅ Rollback completed successfully!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    else:
        run_migration()
