#!/usr/bin/env python3
"""Check all brands in localhost database"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://localhost/tales_db"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT bi.id, bi.brand_name, bi.user_id, u.email
        FROM brand_info bi
        JOIN users u ON bi.user_id = u.id
        ORDER BY bi.id
    """))
    brands = result.fetchall()

    print(f"\n=== All {len(brands)} brands in localhost database ===")
    for brand in brands:
        print(f"Brand ID: {brand[0]}, Name: '{brand[1]}', User: {brand[3]} (ID: {brand[2]})")
