"""Test dashboard and share of voice endpoints"""
import os
os.environ['DATABASE_URL'] = 'postgresql://localhost/tales_db'

from app.database import SessionLocal
from app import analytics

db = SessionLocal()

print("=== TESTING DASHBOARD ===")
dashboard_data = analytics.get_dashboard_metrics(db, user_id=1, brand_id=1)
print("Dashboard keys:", list(dashboard_data.keys()))
print(f"Dashboard data: {dashboard_data}")

print("\n=== TESTING SHARE OF VOICE ===")
sov_data = analytics.get_share_of_voice(db, user_id=1, brand_id=1)
brand_data = next((item for item in sov_data if item.get('is_brand')), None)
if brand_data:
    print(f"SOV Brand keys: {list(brand_data.keys())}")
    print(f"SOV Brand data: {brand_data}")
else:
    print("Brand data not found in SOV response")

db.close()
