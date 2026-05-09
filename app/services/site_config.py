"""
Site Configuration Helper Module

Provides a single source of truth for site-specific configuration values
used in emails and notifications. Falls back to environment variables
if database configuration is not set.
"""
import os
from typing import Optional
from sqlalchemy.orm import Session


def get_site_url(db: Session) -> str:
    """
    Get the configured site URL for email links.

    Priority:
    1. Database configuration (site_url key)
    2. FRONTEND_URL environment variable
    3. Default: http://localhost:5173

    Args:
        db: Database session

    Returns:
        Site URL string (without trailing slash)
    """
    from .. import crud

    # Try database config first
    db_value = crud.get_site_config_value(db, 'site_url')
    if db_value:
        return db_value.rstrip('/')

    # Fall back to environment variable
    env_value = os.getenv('FRONTEND_URL')
    if env_value:
        return env_value.rstrip('/')

    # Default fallback
    return 'http://localhost:5173'


def get_admin_email(db: Session) -> str:
    """
    Get the configured admin contact email for notifications.

    Priority:
    1. Database configuration (admin_email key)
    2. FROM_EMAIL environment variable
    3. Default: (no default, returns empty string)

    Args:
        db: Database session

    Returns:
        Admin email string, or empty string if not configured
    """
    from .. import crud

    # Try database config first
    db_value = crud.get_site_config_value(db, 'admin_email')
    if db_value:
        return db_value

    # Fall back to environment variable
    env_value = os.getenv('FROM_EMAIL')
    if env_value:
        return env_value

    # No default - return empty string
    return ''


def get_site_name(db: Session) -> str:
    """
    Get the configured site/application name.

    Priority:
    1. Database configuration (site_name key)
    2. Default: TALES

    Args:
        db: Database session

    Returns:
        Site name string
    """
    from .. import crud

    # Try database config first
    db_value = crud.get_site_config_value(db, 'site_name')
    if db_value:
        return db_value

    # Default
    return 'TALES'


def get_admin_contact_text(db: Session) -> str:
    """
    Get formatted admin contact text for email footers.

    Returns a string suitable for including in email templates.
    If no admin email is configured, returns a generic message.

    Args:
        db: Database session

    Returns:
        Contact text string for email footers
    """
    admin_email = get_admin_email(db)
    site_name = get_site_name(db)

    if admin_email:
        return f"This is an automated notification from {site_name}. If you have questions, please contact {admin_email}."
    else:
        return f"This is an automated notification from {site_name}."


# --- Branding Configuration for Lab Customization ---

def get_site_logo_url(db: Session) -> Optional[str]:
    """
    Get the configured site logo URL for branding.

    Priority:
    1. Database configuration (site_logo_url key)
    2. SITE_LOGO_URL environment variable
    3. None (no logo)

    Args:
        db: Database session

    Returns:
        Logo URL string or None if not configured
    """
    from .. import crud

    # Try database config first
    db_value = crud.get_site_config_value(db, 'site_logo_url')
    if db_value:
        return db_value

    # Fall back to environment variable
    env_value = os.getenv('SITE_LOGO_URL')
    if env_value:
        return env_value

    # No default
    return None


def get_primary_color(db: Session) -> str:
    """
    Get the configured primary theme color.

    Priority:
    1. Database configuration (primary_color key)
    2. SITE_PRIMARY_COLOR environment variable
    3. Default: #003e60 (PPPL blue)

    Args:
        db: Database session

    Returns:
        Hex color string
    """
    from .. import crud

    # Try database config first
    db_value = crud.get_site_config_value(db, 'primary_color')
    if db_value:
        return db_value

    # Fall back to environment variable
    env_value = os.getenv('SITE_PRIMARY_COLOR')
    if env_value:
        return env_value

    # Default
    return '#003e60'


def get_secondary_color(db: Session) -> str:
    """
    Get the configured secondary theme color.

    Priority:
    1. Database configuration (secondary_color key)
    2. SITE_SECONDARY_COLOR environment variable
    3. Default: #75c9c8 (Tales teal)

    Args:
        db: Database session

    Returns:
        Hex color string
    """
    from .. import crud

    # Try database config first
    db_value = crud.get_site_config_value(db, 'secondary_color')
    if db_value:
        return db_value

    # Fall back to environment variable
    env_value = os.getenv('SITE_SECONDARY_COLOR')
    if env_value:
        return env_value

    # Default
    return '#75c9c8'


def get_branding_config(db: Session) -> dict:
    """
    Get all branding configuration in one call.
    Used by the /site/branding endpoint.

    Args:
        db: Database session

    Returns:
        Dictionary with site_name, site_logo_url, primary_color, secondary_color
    """
    return {
        'site_name': get_site_name(db),
        'site_logo_url': get_site_logo_url(db),
        'primary_color': get_primary_color(db),
        'secondary_color': get_secondary_color(db),
        'admin_email': get_admin_email(db) or None,
    }
