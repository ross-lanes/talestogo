#!/usr/bin/env python3
"""Check localhost PostgreSQL database for data"""
from sqlalchemy import create_engine, inspect, text

# Check localhost postgres (from .env file)
DATABASE_URL = "postgresql://localhost/tales_db"

print(f"Checking localhost PostgreSQL database...")

try:
    engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 5})
    inspector = inspect(engine)

    print("\n=== Tables in localhost postgres ===")
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables")
    for table in tables[:20]:
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
            if 'brand_info' in tables:
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
                for brand in brands:
                    print(f"  Brand ID: {brand[0]}, Name: {brand[1]}, User ID: {brand[2]}")

    print("\n✅ SUCCESS! Found your localhost database with data!")

except Exception as e:
    print(f"\n❌ Error connecting to localhost postgres: {e}")
    print("\nMake sure PostgreSQL is running locally: brew services start postgresql")
