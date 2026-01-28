#!/usr/bin/env python3
"""
Tales Initial Admin Setup Script

Run this script during initial deployment to create the first admin user.
This allows IT teams to set up Tales without requiring OAuth configuration.

Usage:
    # With DATABASE_URL in environment or .env file:
    python scripts/admin/setup_initial_admin.py

    # Or specify DATABASE_URL directly:
    DATABASE_URL=postgresql://user:pass@host:port/db python scripts/admin/setup_initial_admin.py

    # Inside Docker container:
    docker exec -it tales_app python scripts/admin/setup_initial_admin.py
"""

import os
import sys
import secrets
import string

# Preserve DATABASE_URL if explicitly set before loading .env
# This allows: DATABASE_URL=... python script.py
_explicit_db_url = os.environ.get('DATABASE_URL')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)

# Restore explicit DATABASE_URL if it was set
if _explicit_db_url:
    os.environ['DATABASE_URL'] = _explicit_db_url

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import models
from app.auth import get_password_hash


def ensure_tables_exist():
    """Create database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def generate_secure_password(length: int = 16) -> str:
    """Generate a secure random password."""
    # Use letters, digits, and some safe special characters
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure at least one of each type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    # Fill the rest randomly
    password.extend(secrets.choice(alphabet) for _ in range(length - 4))
    # Shuffle to avoid predictable positions
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def check_database_connection() -> bool:
    """Verify database connection works."""
    from sqlalchemy import text
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"\nError: Cannot connect to database.")
        print(f"Details: {e}")
        print("\nMake sure DATABASE_URL is set correctly in your environment or .env file.")
        return False


def check_existing_admins(db: Session) -> list:
    """Check if any admin users already exist."""
    return db.query(models.User).filter(models.User.is_admin == True).all()


def create_admin_user(db: Session, email: str, full_name: str, organization: str, password: str) -> models.User:
    """Create a new admin user with the given credentials."""
    hashed_password = get_password_hash(password)

    user = models.User(
        email=email,
        full_name=full_name,
        organization=organization,
        hashed_password=hashed_password,
        is_admin=True,
        is_active=True,
        is_invited=True,
        allowed_products="tales,heads,canon",  # Full access to all products
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main():
    print("=" * 60)
    print("TALES Initial Admin Setup")
    print("=" * 60)
    print()

    # Check database connection
    print("Checking database connection...")
    if not check_database_connection():
        sys.exit(1)
    print("Database connection OK.")

    # Ensure tables exist (for fresh databases)
    print("Ensuring database tables exist...")
    ensure_tables_exist()
    print("Database ready.")
    print()

    db = SessionLocal()

    try:
        # Check for existing admins
        existing_admins = check_existing_admins(db)
        if existing_admins:
            print("WARNING: Admin user(s) already exist:")
            for admin in existing_admins:
                print(f"  - {admin.email} ({admin.full_name})")
            print()
            response = input("Do you want to create another admin? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Exiting without changes.")
                return
            print()

        # Get admin details
        print("Enter details for the new admin user:")
        print("-" * 40)

        email = input("Email address: ").strip()
        if not email or '@' not in email:
            print("Error: Invalid email address.")
            sys.exit(1)

        # Check if email already exists
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            print(f"Error: A user with email '{email}' already exists.")
            sys.exit(1)

        full_name = input("Full name: ").strip()
        if not full_name:
            print("Error: Full name is required.")
            sys.exit(1)

        organization = input("Organization (optional, press Enter to skip): ").strip()

        # Generate secure password
        password = generate_secure_password(16)

        print()
        print("Creating admin user...")

        user = create_admin_user(db, email, full_name, organization, password)

        print()
        print("=" * 60)
        print("SUCCESS! Admin user created.")
        print("=" * 60)
        print()
        print("IMPORTANT: Save these credentials securely. The password")
        print("will not be shown again.")
        print()
        print("-" * 60)
        print(f"Email:    {email}")
        print(f"Password: {password}")
        print("-" * 60)
        print()
        print("Next steps:")
        print("1. Share these credentials securely with the designated admin")
        print("2. Admin should log in at your Tales URL")
        print("3. After logging in, change password via Settings page")
        print("4. Admin can then invite other users via Admin Panel")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
