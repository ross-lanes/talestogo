#!/usr/bin/env python3
"""Check what tables exist in production database"""
from sqlalchemy import create_engine, inspect

# Use production database
DATABASE_URL = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@tramway.proxy.rlwy.net:47287/railway"

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("\n=== Tables in production database ===")
tables = inspector.get_table_names()
print(f"Found {len(tables)} tables:")
for table in tables:
    print(f"  - {table}")

# Check for users with robotrachel@gmail.com
if 'users' in tables:
    print("\n=== Checking users table ===")
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, email, google_id, tenant_id FROM users WHERE email = 'robotrachel@gmail.com'"))
        users = result.fetchall()
        print(f"Found {len(users)} user(s) with email robotrachel@gmail.com")
        for user in users:
            print(f"  User ID: {user[0]}, Email: {user[1]}, Google ID: {user[2]}, Tenant ID: {user[3]}")

        # Check total brands
        result = conn.execute(text("SELECT COUNT(*) FROM brand_info"))
        count = result.scalar()
        print(f"\nTotal brands in database: {count}")

        # Check brands for robotrachel@gmail.com users
        result = conn.execute(text("""
            SELECT bi.id, bi.brand_name, bi.user_id, u.email
            FROM brand_info bi
            JOIN users u ON bi.user_id = u.id
            WHERE u.email = 'robotrachel@gmail.com'
        """))
        brands = result.fetchall()
        print(f"\nBrands for robotrachel@gmail.com: {len(brands)}")
        for brand in brands:
            print(f"  Brand ID: {brand[0]}, Name: {brand[1]}, User ID: {brand[2]}, Email: {brand[3]}")
