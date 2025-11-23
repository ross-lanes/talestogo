#!/usr/bin/env python3
"""Check Render database for data"""
from sqlalchemy import create_engine, inspect, text

# Try the Render database URL from .env
DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

print(f"Connecting to Render database...")

try:
    engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 10})
    inspector = inspect(engine)

    print("\n=== Tables in Render database ===")
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")

    # Check for users with robotrachel@gmail.com
    if 'users' in tables:
        print("\n=== Checking users table ===")
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
                ORDER BY bi.id
            """))
            brands = result.fetchall()
            print(f"\nBrands for robotrachel@gmail.com: {len(brands)}")
            for brand in brands[:10]:  # Show first 10
                print(f"  Brand ID: {brand[0]}, Name: {brand[1]}, User ID: {brand[2]}")

            if len(brands) > 10:
                print(f"  ... and {len(brands) - 10} more brands")

    print("\n✅ SUCCESS! This is the database with your data!")

except Exception as e:
    print(f"\n❌ Error: {e}")
