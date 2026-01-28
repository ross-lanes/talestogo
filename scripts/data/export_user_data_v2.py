#!/usr/bin/env python3
"""
Export data for a specific user using SQLite's iterdump.
This is more robust than manual SQL generation.
"""

import sqlite3
import sys
from pathlib import Path

def export_user_data(db_path, user_email, output_file):
    """Export all data for a specific user using SQLite dump."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get user ID
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    user_row = cursor.fetchone()
    if not user_row:
        print(f"Error: User {user_email} not found in database")
        return False

    user_id = user_row[0]
    print(f"Found user {user_email} with ID {user_id}")

    # Create a temporary database with just this user's data
    temp_db = Path(__file__).parent / "temp_export.db"
    if temp_db.exists():
        temp_db.unlink()

    temp_conn = sqlite3.connect(temp_db)
    temp_cursor = temp_conn.cursor()

    # Copy schema from original database
    for line in conn.iterdump():
        if line.startswith('CREATE TABLE') or line.startswith('CREATE INDEX'):
            # Skip migration tracking table
            if 'schema_migrations' not in line:
                try:
                    temp_cursor.execute(line)
                except sqlite3.OperationalError:
                    pass  # Table might already exist

    temp_conn.commit()

    # Tables and their relationships
    tables = [
        ('users', 'id', user_id),
        ('brand_info', 'user_id', user_id),
        ('competitors', 'user_id', user_id),
        ('target_descriptors', 'user_id', user_id),
        ('queries', 'user_id', user_id),
        ('responses', 'user_id', user_id),
        ('cited_sources', 'user_id', user_id),
        ('campaigns', 'user_id', user_id),
        ('reports', 'user_id', user_id),
        ('task_status', 'user_id', user_id),
        ('trends', 'user_id', user_id),
        ('analyses', 'user_id', user_id),
    ]

    total_rows = 0
    for table_name, id_column, id_value in tables:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            print(f"  ⊘ Table {table_name} does not exist (skipped)")
            continue

        # Copy data
        cursor.execute(f"SELECT * FROM {table_name} WHERE {id_column} = ?", (id_value,))
        rows = cursor.fetchall()

        if rows:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            # Insert into temp database
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

            for row in rows:
                temp_cursor.execute(insert_sql, row)

            temp_conn.commit()
            total_rows += len(rows)
            print(f"  ✓ Exported {len(rows)} rows from {table_name}")
        else:
            print(f"  - No data in {table_name}")

    # Generate SQL dump from temp database
    with open(output_file, 'w') as f:
        f.write("-- Data export for user: {}\n".format(user_email))
        f.write("-- Generated with export_user_data_v2.py\n\n")
        f.write("BEGIN TRANSACTION;\n\n")
        f.write("-- Delete existing user data if present\n")
        f.write("DELETE FROM users WHERE email = '{}';\n\n".format(user_email.replace("'", "''")))

        # Only dump INSERT statements
        for line in temp_conn.iterdump():
            if line.startswith('INSERT INTO'):
                # Skip migration tracking
                if 'schema_migrations' not in line:
                    f.write(line + '\n')

        f.write("\nCOMMIT;\n")

    # Cleanup
    temp_conn.close()
    temp_db.unlink()
    conn.close()

    print(f"\n✓ Export complete: {total_rows} total rows exported to {output_file}")
    return True

if __name__ == "__main__":
    db_path = Path(__file__).parent / "tales.db"
    user_email = "robotrachel@gmail.com"
    output_file = Path(__file__).parent / "user_data_export_v2.sql"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    success = export_user_data(db_path, user_email, output_file)
    sys.exit(0 if success else 1)
