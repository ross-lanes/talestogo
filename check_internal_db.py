#!/usr/bin/env python3
"""Check what tables exist in internal database URL"""
from sqlalchemy import create_engine, inspect

# Try internal database URL (this won't work from outside Railway, but let's check the format)
DATABASE_URL = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@postgres.railway.internal:5432/railway"

print("NOTE: This will fail from outside Railway network, but showing what would be checked...")
print(f"Attempting to connect to: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 5})
    inspector = inspect(engine)

    print("\n=== Tables in internal database ===")
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")
except Exception as e:
    print(f"\nExpected error (cannot connect from outside Railway): {e}")
    print("\nThe app running IN Railway would use the internal URL.")
    print("We need to use the PUBLIC URL from outside Railway.")
