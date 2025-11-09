"""
Create a new tenant

This script creates a new tenant in the database.

Usage:
    python migrations/create_tenant.py "Company Name" --primary-color "#FF5733" --secondary-color "#3357FF"
"""

import sys
import os
import argparse

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models

def create_tenant(
    tenant_name: str,
    subdomain: str = None,
    primary_color: str = "#75C9C8",
    secondary_color: str = "#665775",
    logo_url: str = None,
    custom_domain: str = None
):
    """Create a new tenant."""
    db = SessionLocal()

    try:
        # Check if tenant already exists
        existing = db.query(models.Tenant).filter(
            models.Tenant.tenant_name == tenant_name
        ).first()

        if existing:
            print(f"✗ Tenant '{tenant_name}' already exists (ID: {existing.id})")
            return

        # Create new tenant
        new_tenant = models.Tenant(
            tenant_name=tenant_name,
            subdomain=subdomain,
            logo_url=logo_url,
            primary_color=primary_color,
            secondary_color=secondary_color,
            custom_domain=custom_domain
        )
        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)

        print("=" * 60)
        print(f"✓ Successfully created tenant: {tenant_name}")
        print("=" * 60)
        print(f"  ID: {new_tenant.id}")
        print(f"  Name: {new_tenant.tenant_name}")
        print(f"  Subdomain: {new_tenant.subdomain or 'None'}")
        print(f"  Primary Color: {new_tenant.primary_color}")
        print(f"  Secondary Color: {new_tenant.secondary_color}")
        print(f"  Logo URL: {new_tenant.logo_url or 'None'}")
        print(f"  Custom Domain: {new_tenant.custom_domain or 'None'}")
        print("=" * 60)
        print()
        print(f"Tenant ID {new_tenant.id} can now be used when inviting users!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a new tenant')
    parser.add_argument('tenant_name', help='Name of the tenant (e.g., "Company X")')
    parser.add_argument('--subdomain', help='Subdomain (e.g., "companyx")')
    parser.add_argument('--primary-color', default='#75C9C8', help='Primary brand color (hex)')
    parser.add_argument('--secondary-color', default='#665775', help='Secondary brand color (hex)')
    parser.add_argument('--logo-url', help='URL to company logo')
    parser.add_argument('--custom-domain', help='Custom domain (e.g., "tales.companyx.com")')

    args = parser.parse_args()

    print()
    create_tenant(
        tenant_name=args.tenant_name,
        subdomain=args.subdomain,
        primary_color=args.primary_color,
        secondary_color=args.secondary_color,
        logo_url=args.logo_url,
        custom_domain=args.custom_domain
    )
