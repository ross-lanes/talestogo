"""
Script to clean up competitor names by replacing commas within organization names.

This prevents issues when splitting competitor lists by comma.
Examples:
- "UKAEA (MAST-U, STEP)" -> "UKAEA (MAST-U and STEP)"
- "Company, Inc." -> "Company Inc."
"""
from app.database import SessionLocal
from app.models import Response

def clean_competitor_name(name: str) -> str:
    """
    Clean a single competitor name by replacing commas with appropriate alternatives.

    Args:
        name: Competitor name that may contain commas

    Returns:
        Cleaned competitor name
    """
    # Common patterns to replace
    replacements = {
        '(MAST-U, STEP)': '(MAST-U and STEP)',
        ', Inc.': ' Inc.',
        ', LLC': ' LLC',
        ', Ltd.': ' Ltd.',
        ', Corp.': ' Corp.',
    }

    cleaned = name
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    return cleaned

def clean_all_competitor_names():
    """Clean competitor names in all responses."""
    db = SessionLocal()

    try:
        # Get all responses with competitors
        responses = db.query(Response).filter(Response.competitors.isnot(None)).all()

        updated_count = 0

        for response in responses:
            if response.competitors:
                # Split by comma, clean each name, rejoin
                competitors_list = [comp.strip() for comp in response.competitors.split(',')]
                cleaned_list = [clean_competitor_name(comp) for comp in competitors_list]

                new_competitors = ', '.join(cleaned_list)

                if new_competitors != response.competitors:
                    print(f"Updating: {response.competitors[:100]}")
                    print(f"      To: {new_competitors[:100]}")
                    response.competitors = new_competitors
                    updated_count += 1

        db.commit()
        print(f"\nUpdated {updated_count} responses")

    finally:
        db.close()

if __name__ == "__main__":
    clean_all_competitor_names()
