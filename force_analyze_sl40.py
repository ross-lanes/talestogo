"""
Force analysis for sl40@princeton.edu on PRODUCTION database
"""
import os
import sys

# Set production database URL
PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"
os.environ['DATABASE_URL'] = PROD_DATABASE_URL

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Response, User, BrandInfo

# Connect to production
engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("\n" + "="*80)
print("FORCE ANALYZE sl40@princeton.edu - Princeton Engineering")
print("="*80 + "\n")

# Find user and brand
user = db.query(User).filter_by(email="sl40@princeton.edu").first()
if not user:
    print("❌ User not found")
    sys.exit(1)

brand = db.query(BrandInfo).filter_by(user_id=user.id, brand_name="Princeton Engineering").first()
if not brand:
    print("❌ Brand not found")
    sys.exit(1)

print(f"User ID: {user.id}")
print(f"Brand ID: {brand.id}")
print(f"Brand Name: {brand.brand_name}\n")

# Get unanalyzed responses
unanalyzed = db.query(Response).filter(
    Response.user_id == user.id,
    Response.brand_id == brand.id,
    Response.analyzed_at.is_(None)
).all()

print(f"Found {len(unanalyzed)} unanalyzed responses\n")

if len(unanalyzed) == 0:
    print("✅ All responses already analyzed!")
    db.close()
    sys.exit(0)

# Import the analyzer
from scripts.admin.analyze_responses import ResponseAnalyzer

print("Starting analysis...")
analyzer = ResponseAnalyzer(db, user.id, brand.id, task_status_id=0)

# Analyze each response
for i, response in enumerate(unanalyzed, 1):
    print(f"\rAnalyzing {i}/{len(unanalyzed)}...", end="", flush=True)
    try:
        analysis_data = analyzer.analyze_response(response)
        if analysis_data:
            analyzer.save_analysis(response, analysis_data)
    except Exception as e:
        print(f"\n❌ Error analyzing response {response.id}: {e}")

print(f"\n\n✅ Analysis complete!")

# Check results
analyzed_count = db.query(Response).filter(
    Response.user_id == user.id,
    Response.brand_id == brand.id,
    Response.analyzed_at.isnot(None)
).count()

print(f"Total analyzed: {analyzed_count}")

db.close()
