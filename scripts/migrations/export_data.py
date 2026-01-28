#!/usr/bin/env python3
"""
Export important data from local SQLite database to JSON for manual review and import.
"""

import json
import sqlite3
from datetime import datetime

def export_data():
    """Export data from SQLite to JSON files."""
    conn = sqlite3.connect('tales.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()

    print("Exporting data from tales.db...\n")

    # Export users
    cursor.execute("SELECT * FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    print(f"✓ Exported {len(users)} users")

    # Export brand_info
    cursor.execute("SELECT * FROM brand_info")
    brands = [dict(row) for row in cursor.fetchall()]
    print(f"✓ Exported {len(brands)} brands")

    # Export queries
    cursor.execute("SELECT * FROM queries")
    queries = [dict(row) for row in cursor.fetchall()]
    print(f"✓ Exported {len(queries)} queries")

    # Export responses
    cursor.execute("SELECT * FROM responses")
    responses = [dict(row) for row in cursor.fetchall()]
    print(f"✓ Exported {len(responses)} responses")

    # Export competitors
    cursor.execute("SELECT * FROM competitors")
    competitors = [dict(row) for row in cursor.fetchall()]
    print(f"✓ Exported {len(competitors)} competitors")

    # Export target_descriptors
    cursor.execute("SELECT * FROM target_descriptors")
    descriptors = [dict(row) for row in cursor.fetchall()]
    print(f"✓ Exported {len(descriptors)} target descriptors")

    # Export reports
    cursor.execute("SELECT * FROM reports")
    reports = [dict(row) for row in cursor.fetchall()]
    print(f"✓ Exported {len(reports)} reports")

    conn.close()

    # Create export package
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "source": "tales.db (local SQLite)",
        "users": users,
        "brands": brands,
        "queries": queries,
        "responses": responses,
        "competitors": competitors,
        "target_descriptors": descriptors,
        "reports": reports,
    }

    # Save to JSON
    filename = f"tales_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"\n✅ Data exported to: {filename}")
    print(f"\nSummary:")
    print(f"  • {len(users)} users")
    print(f"  • {len(brands)} brands")
    print(f"  • {len(queries)} queries")
    print(f"  • {len(responses)} responses")
    print(f"  • {len(competitors)} competitors")
    print(f"  • {len(descriptors)} target descriptors")
    print(f"  • {len(reports)} reports")
    print(f"\nTotal records: {sum([len(users), len(brands), len(queries), len(responses), len(competitors), len(descriptors), len(reports)])}")

if __name__ == "__main__":
    export_data()
