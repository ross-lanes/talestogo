"""
Diagnostic script to check Virelyxa brand status and reports.
Run this on Render to see why recommendations aren't showing.
"""
import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models

def main():
    db = SessionLocal()

    try:
        print("=" * 60)
        print("VIRELYXA DIAGNOSTIC REPORT")
        print("=" * 60)

        # 1. Find the user
        user = db.query(models.User).filter(models.User.email == "robotrachel@gmail.com").first()
        if not user:
            print("❌ ERROR: User robotrachel@gmail.com not found!")
            return

        print(f"\n✓ User found: {user.email} (ID: {user.id})")

        # 2. Find all brands for this user
        brands = db.query(models.BrandInfo).filter(
            models.BrandInfo.user_id == user.id
        ).all()

        print(f"\n📊 Total brands for user: {len(brands)}")
        print("-" * 60)

        virelyxa_brand = None
        for brand in brands:
            is_virelyxa = brand.brand_name == "Virelyxa"
            marker = "👉" if is_virelyxa else "  "
            print(f"{marker} Brand: {brand.brand_name}")
            print(f"   - ID: {brand.id}")
            print(f"   - is_active: {brand.is_active}")
            print(f"   - Created: {brand.created_at}")

            if is_virelyxa:
                virelyxa_brand = brand

        if not virelyxa_brand:
            print("\n❌ ERROR: Virelyxa brand not found!")
            return

        print(f"\n✓ Virelyxa brand found (ID: {virelyxa_brand.id})")

        # 3. Check what brand is currently active
        active_brand = db.query(models.BrandInfo).filter(
            models.BrandInfo.user_id == user.id,
            models.BrandInfo.is_active == True
        ).first()

        if active_brand:
            print(f"\n🎯 Currently active brand: {active_brand.brand_name} (ID: {active_brand.id})")
            if active_brand.id != virelyxa_brand.id:
                print(f"   ⚠️  WARNING: Active brand is NOT Virelyxa!")
        else:
            print(f"\n⚠️  WARNING: No active brand set for this user!")

        # 4. Check reports for Virelyxa
        reports = db.query(models.Report).filter(
            models.Report.brand_id == virelyxa_brand.id,
            models.Report.user_id == user.id
        ).order_by(models.Report.created_at.desc()).all()

        print(f"\n📄 Reports for Virelyxa: {len(reports)}")
        print("-" * 60)

        for i, report in enumerate(reports, 1):
            print(f"{i}. {report.title}")
            print(f"   - Created: {report.created_at}")
            print(f"   - Has '## 4. Strategic Recommendations': {'## 4. Strategic Recommendations' in report.report_content}")

        # 5. Check what the recommendations endpoint would return
        print(f"\n🔍 Simulating /analytics/recommendations endpoint...")
        print("-" * 60)

        # This mimics what the endpoint does
        query = db.query(models.Report).filter(models.Report.user_id == user.id)

        if active_brand:
            print(f"   Filtering by active brand: {active_brand.brand_name} (ID: {active_brand.id})")
            query = query.filter(models.Report.brand_id == active_brand.id)
        else:
            print(f"   No active brand - querying all reports for user")

        latest_report = query.order_by(models.Report.created_at.desc()).first()

        if latest_report:
            print(f"\n✓ Latest report found:")
            print(f"   - Title: {latest_report.title}")
            print(f"   - Brand ID: {latest_report.brand_id}")
            print(f"   - Created: {latest_report.created_at}")

            if "## 4. Strategic Recommendations" in latest_report.report_content:
                print(f"   ✓ Contains '## 4. Strategic Recommendations' section")
            else:
                print(f"   ❌ Does NOT contain '## 4. Strategic Recommendations' section")
        else:
            print(f"\n❌ No reports found!")

        # 6. Recommendations
        print(f"\n💡 DIAGNOSIS:")
        print("=" * 60)

        if not virelyxa_brand.is_active:
            print("❌ ISSUE: Virelyxa is_active = False")
            print("   FIX: Run populate_virelyxa_demo_data.py again (updated version sets is_active=True)")

        if active_brand and active_brand.id != virelyxa_brand.id:
            print(f"❌ ISSUE: A different brand ('{active_brand.brand_name}') is set as active")
            print(f"   FIX: In the UI, select Virelyxa from the brand dropdown")

        if not active_brand:
            print(f"❌ ISSUE: No brand is set as active")
            print(f"   FIX: Run populate_virelyxa_demo_data.py to set Virelyxa as active")

        if len(reports) == 0:
            print(f"❌ ISSUE: No reports exist for Virelyxa")
            print(f"   FIX: Run populate_virelyxa_demo_data.py to generate demo data")

        if active_brand and active_brand.id == virelyxa_brand.id and len(reports) > 0:
            print(f"✓ Everything looks good! Reports should be visible.")
            print(f"   If still not showing, check browser console for errors.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
