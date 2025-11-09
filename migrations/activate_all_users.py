#!/usr/bin/env python3
"""
Migration Script: Activate All Users
Purpose: Set is_active=True for all existing users to enable login

This script should be run once on production to activate all user accounts
that were created before this authentication fix.

Usage:
    python migrations/activate_all_users.py
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User
from app.auth import get_oauth_provider_for_email


def activate_all_users():
    """Activate all users and set OAuth providers based on email domain"""
    db = SessionLocal()

    try:
        # Get all users
        users = db.query(User).all()

        print(f'\n{"="*60}')
        print(f'User Activation Migration')
        print(f'{"="*60}\n')
        print(f'Total users found: {len(users)}\n')

        activated_count = 0
        oauth_updated_count = 0

        for user in users:
            changes = []

            # Activate user if not already active
            if not user.is_active:
                user.is_active = True
                activated_count += 1
                changes.append('activated')

            # Set OAuth provider based on email domain if not set
            if not user.oauth_provider:
                oauth_provider = get_oauth_provider_for_email(user.email)
                if oauth_provider:
                    user.oauth_provider = oauth_provider
                    oauth_updated_count += 1
                    changes.append(f'oauth_provider={oauth_provider}')

            if changes:
                print(f'✓ Updated {user.email}: {", ".join(changes)}')
            else:
                print(f'  {user.email}: already configured')

        # Commit all changes
        db.commit()

        print(f'\n{"="*60}')
        print(f'Migration Complete!')
        print(f'{"="*60}')
        print(f'Users activated: {activated_count}')
        print(f'OAuth providers set: {oauth_updated_count}')
        print(f'\nAll users can now login! 🎉\n')

        return True

    except Exception as e:
        db.rollback()
        print(f'\n❌ Error during migration: {str(e)}')
        return False

    finally:
        db.close()


if __name__ == '__main__':
    print('\nStarting user activation migration...\n')
    success = activate_all_users()
    sys.exit(0 if success else 1)
