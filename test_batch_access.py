"""
Test script to verify batch access works for shared brands
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models
from app.utils.brand_access import get_data_owner_user_id

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_batch_access():
    db = SessionLocal()
    try:
        # Test data:
        # Scott Lyon user_id=15, owns Princeton Engineering brand_id=14
        # Admin (you) has shared access to Princeton Engineering

        # Get admin user
        admin = db.query(models.User).filter(models.User.is_admin == True).first()
        print(f"Admin User ID: {admin.id}, Email: {admin.email}")

        # Test: Get data owner for Princeton Engineering brand
        brand_id = 14  # Princeton Engineering

        # First, verify the brand exists in the database
        brand = db.query(models.BrandInfo).filter_by(id=brand_id).first()
        print(f"\nBrand lookup: {brand}")
        if brand:
            print(f"  Brand ID: {brand.id}, Name: {brand.brand_name}, Owner: {brand.user_id}")

        try:
            data_owner_user_id = get_data_owner_user_id(db, brand_id, admin.id)
            print(f"\nBrand ID {brand_id} (Princeton Engineering)")
            print(f"Data Owner User ID: {data_owner_user_id}")
            print(f"Expected: 15 (Scott Lyon)")
        except Exception as e:
            print(f"\nError calling get_data_owner_user_id: {e}")
            import traceback
            traceback.print_exc()
            return

        # Fetch batches using the data owner's user_id
        batches = db.query(models.CollectionBatch).filter_by(
            user_id=data_owner_user_id,
            brand_id=brand_id
        ).order_by(models.CollectionBatch.started_at.desc()).all()

        print(f"\nBatches found: {len(batches)}")
        for batch in batches[:5]:  # Show first 5
            print(f"  Batch ID: {batch.id}, Name: {batch.batch_name}, Started: {batch.started_at}, Status: {batch.status}")

        if len(batches) > 0:
            print("\n✅ SUCCESS: Batches are accessible for shared brand!")
        else:
            print("\n❌ FAIL: No batches found")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_batch_access()
