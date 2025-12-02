"""
Timezone utility functions for consistent EST/EDT handling across the application.
All user-facing dates should be displayed in Eastern Time.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

# Eastern timezone (handles EST/EDT automatically)
EASTERN_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")


def now_eastern() -> datetime:
    """Get current datetime in Eastern timezone."""
    return datetime.now(EASTERN_TZ)


def utc_to_eastern(dt: datetime) -> datetime:
    """
    Convert a UTC datetime to Eastern timezone.

    Args:
        dt: A datetime object (naive assumed UTC, or timezone-aware)

    Returns:
        Datetime in Eastern timezone
    """
    if dt is None:
        return None

    # If naive datetime, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)

    return dt.astimezone(EASTERN_TZ)


def format_eastern(dt: datetime, format_str: str = "%B %d, %Y at %I:%M %p") -> str:
    """
    Format a datetime in Eastern timezone.

    Args:
        dt: A datetime object
        format_str: strftime format string (default: "January 1, 2024 at 3:45 PM")

    Returns:
        Formatted string in Eastern timezone
    """
    if dt is None:
        return ""

    eastern_dt = utc_to_eastern(dt)
    return eastern_dt.strftime(format_str)


def format_eastern_short(dt: datetime) -> str:
    """Format datetime as short date in Eastern timezone (Jan 1, 2024)."""
    return format_eastern(dt, "%b %d, %Y")


def format_eastern_date(dt: datetime) -> str:
    """Format datetime as date only in Eastern timezone (2024-01-01)."""
    return format_eastern(dt, "%Y-%m-%d")


def format_eastern_datetime(dt: datetime) -> str:
    """Format datetime with time in Eastern timezone (January 1, 2024 at 3:45 PM EST)."""
    if dt is None:
        return ""

    eastern_dt = utc_to_eastern(dt)
    # Get timezone abbreviation (EST or EDT)
    tz_abbr = eastern_dt.strftime("%Z")
    return eastern_dt.strftime(f"%B %d, %Y at %I:%M %p {tz_abbr}")
