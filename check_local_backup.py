#!/usr/bin/env python3
"""Check local SQLite backup for data"""
from sqlalchemy import create_engine, inspect, text

# Check the October 31 backup
DATABASE_URL = "sqlite:////Users/rachelkremen/Documents/Code/tales_project/tales.backup_20251031_080819.db"

print(f"Checking backup from October 31...")

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    print("\n=== Tables in backup database ===")
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables")

    # Check for users with robotrachel@gmail.com
    if 'users' in tables:
        print("\n=== Checking users table ===")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, email, google_id FROM users WHERE email = 'robotrachel@gmail.com'"))
            users = result.fetchall()
            print(f"Found {len(users)} user(s) with email robotrachel@gmail.com")
            for user in users:
                print(f"  User ID: {user[0]}, Email: {user[1]}, Google ID: {user[2]}")

            # Check total brands
            if 'brand_info' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM brand_info"))
                count = result.scalar()
                print(f"\nTotal brands in backup: {count}")

                # Check brands for robotrachel@gmail.com users
                result = conn.execute(text("""
                    SELECT bi.id, bi.brand_name, bi.user_id, u.email
                    FROM brand_info bi
                    JOIN users u ON bi.user_id = u.id
                    WHERE u.email = 'robotrachel@gmail.com'
                    ORDER BY bi.id
                """))
                brands = result.fetchall()
                print(f"\nBrands for robotrachel@gmail.com in backup: {len(brands)}")
                for brand in brands[:10]:
                    print(f"  Brand ID: {brand[0]}, Name: {brand[1]}, User ID: {brand[2]}")

                if len(brands) > 10:
                    print(f"  ... and {len(brands) - 10} more brands")

    print("\n✅ Backup check complete!")

except Exception as e:
    print(f"\n❌ Error: {e}")
