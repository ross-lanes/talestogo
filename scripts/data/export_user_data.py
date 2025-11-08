#!/usr/bin/env python3
"""
Export data for a specific user from the local database.
This creates a SQL file that can be imported into production.
"""

import sqlite3
import sys
from pathlib import Path

def export_user_data(db_path, user_email, output_file):
    """Export all data for a specific user."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get user ID
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    user_row = cursor.fetchone()
    if not user_row:
        print(f"Error: User {user_email} not found in database")
        return False

    user_id = user_row['id']
    print(f"Found user {user_email} with ID {user_id}")

    # Tables to export (in dependency order)
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

    with open(output_file, 'w') as f:
        f.write("-- Data export for user: {}\n".format(user_email))
        f.write("-- Generated: {}\n\n".format(Path(__file__).name))
        f.write("BEGIN TRANSACTION;\n\n")

        # First, delete existing user if exists (to avoid conflicts)
        f.write("-- Delete existing user data if present\n")
        f.write("DELETE FROM users WHERE email = '{}';\n\n".format(user_email))

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

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col['name'] for col in cursor.fetchall()]

            # Get data
            cursor.execute(
                f"SELECT * FROM {table_name} WHERE {id_column} = ?",
                (id_value,)
            )
            rows = cursor.fetchall()

            if rows:
                f.write(f"-- Export {table_name} ({len(rows)} rows)\n")
                for row in rows:
                    # Build INSERT statement
                    col_list = ', '.join(columns)
                    # Escape single quotes in values
                    values = []
                    for val in row:
                        if val is None:
                            values.append('NULL')
                        elif isinstance(val, str):
                            # Escape single quotes
                            escaped = val.replace("'", "''")
                            values.append(f"'{escaped}'")
                        else:
                            values.append(str(val))
                    val_list = ', '.join(values)

                    f.write(f"INSERT INTO {table_name} ({col_list}) VALUES ({val_list});\n")

                f.write("\n")
                total_rows += len(rows)
                print(f"  ✓ Exported {len(rows)} rows from {table_name}")
            else:
                print(f"  - No data in {table_name}")

        f.write("COMMIT;\n")

    conn.close()
    print(f"\n✓ Export complete: {total_rows} total rows exported to {output_file}")
    return True

if __name__ == "__main__":
    db_path = Path(__file__).parent / "tales.db"
    user_email = "robotrachel@gmail.com"
    output_file = Path(__file__).parent / "user_data_export.sql"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    success = export_user_data(db_path, user_email, output_file)
    sys.exit(0 if success else 1)
