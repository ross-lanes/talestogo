#!/usr/bin/env python3
"""Check user account and associated brands"""
import sys
from app.database import SessionLocal
from app.models import User, BrandInfo, Tenant

def check_user_brands(email: str):
    db = SessionLocal()

    try:
        # Find all users with this email
        users = db.query(User).filter(User.email == email).all()

        print(f"\n=== Users with email: {email} ===")
        print(f"Found {len(users)} user(s)\n")

        for user in users:
            print(f"User ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Full Name: {user.full_name}")
            print(f"Is Active: {user.is_active}")
            print(f"Is Admin: {user.is_admin}")
            print(f"Tenant ID: {user.tenant_id}")

            # Get tenant info
            if user.tenant_id:
                tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
                if tenant:
                    print(f"Tenant Name: {tenant.tenant_name}")

            print(f"Google ID: {user.google_id}")
            print(f"Microsoft ID: {user.microsoft_id}")
            print(f"OAuth Provider: {user.oauth_provider}")

            # Get brands for this user
            brands = db.query(BrandInfo).filter(BrandInfo.user_id == user.id).all()
            print(f"\nBrands for this user: {len(brands)}")
            for brand in brands:
                print(f"  - ID: {brand.id}, Name: {brand.brand_name}, Active: {brand.is_active}")

            print("\n" + "="*50 + "\n")

        # Also check for brands with email in the query
        print(f"=== All brands in database ===")
        all_brands = db.query(BrandInfo).all()
        print(f"Total brands: {len(all_brands)}")
        for brand in all_brands[:20]:  # Show first 20
            user = db.query(User).filter(User.id == brand.user_id).first()
            print(f"Brand: {brand.brand_name} (ID: {brand.id})")
            print(f"  User ID: {brand.user_id}, Email: {user.email if user else 'N/A'}")
            print(f"  Active: {brand.is_active}")

    finally:
        db.close()

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "robotrachel@gmail.com"
    check_user_brands(email)
