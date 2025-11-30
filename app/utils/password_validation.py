"""
Password validation utilities for enforcing strong password requirements.
"""
import re
from typing import List, Tuple


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength against security requirements.

    Password requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character (!@#$%^&*(),.?":{}|<>)

    Args:
        password: The password to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
        - is_valid: True if password meets all requirements
        - list_of_errors: List of requirement violations (empty if valid)
    """
    errors = []

    # Check minimum length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    # Check for number
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")

    is_valid = len(errors) == 0
    return is_valid, errors


def get_password_requirements_message() -> str:
    """
    Get a formatted message describing password requirements.

    Returns:
        String describing all password requirements
    """
    return (
        "Password requirements:\n"
        "  • At least 8 characters long\n"
        "  • Contains at least one uppercase letter (A-Z)\n"
        "  • Contains at least one lowercase letter (a-z)\n"
        "  • Contains at least one number (0-9)\n"
        "  • Contains at least one special character (!@#$%^&*(),.?\":{}|<>)"
    )


def format_password_errors(errors: List[str]) -> str:
    """
    Format a list of password validation errors into a single message.

    Args:
        errors: List of error messages

    Returns:
        Formatted error message string
    """
    if not errors:
        return ""

    error_message = "Password does not meet security requirements:\n"
    for error in errors:
        error_message += f"  • {error}\n"

    return error_message.strip()
