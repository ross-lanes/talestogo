#!/usr/bin/env python3
"""
Find all brands owned by robotrachel@gmail.com
"""
import sys
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # Find user by email
    result = db.execute(text("SELECT id, email FROM users WHERE email = 'robotrachel@gmail.com'"))
    user = result.fetchone()

    if not user:
        print("User robotrachel@gmail.com not found")
        sys.exit(1)

    user_id = user[0]
    print(f"Found user: {user[1]} (ID: {user_id})\n")

    # Find all brands for this user
    result = db.execute(text("SELECT id, brand_name FROM brand_info WHERE user_id = :user_id ORDER BY id"), {"user_id": user_id})
    brands = result.fetchall()

    if not brands:
        print("No brands found for this user")
        sys.exit(1)

    print(f"Found {len(brands)} brands:\n")
    for brand_id, brand_name in brands:
        print(f"Brand: {brand_name}")
        print(f"  Brand ID: {brand_id}")
        print(f"  User ID: {user_id}")
        print()

        # Check for Princeton Plasma or Oak Ridge
        if "Princeton Plasma" in brand_name or "Oak Ridge" in brand_name:
            print(f"  *** Target brand for report regeneration ***")
            print(f"  Command: python3 scripts/admin/generate_report.py --user-id {user_id} --brand-id {brand_id}")
            print()

finally:
    db.close()
