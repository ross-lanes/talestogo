#!/usr/bin/env python3
"""
Migration: Add Heads (Persona Intelligence Platform) tables for SAS integration

This migration:
1. Creates persona_generations table
2. Creates personas table
3. Creates indexes for performance
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """Run the Heads tables migration"""

    with engine.connect() as conn:
        print("Starting Heads tables migration...")
        print()

        # Step 1: Create persona_generations table
        print("1. Creating persona_generations table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS persona_generations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                brand_id INTEGER NOT NULL REFERENCES brand_info(id),

                -- Patient generation parameters
                patient_occupation VARCHAR(200),
                patient_diagnosis VARCHAR(200),
                patient_gender VARCHAR(50),
                patient_symptoms TEXT,
                patient_age_range VARCHAR(50),

                -- HCP generation parameters
                hcp_type VARCHAR(200),
                hcp_disease_focus VARCHAR(200),
                hcp_location VARCHAR(200),

                -- Output
                pptx_file_path VARCHAR(500),
                pptx_file_url VARCHAR(500),

                -- Status tracking
                status VARCHAR(20) DEFAULT 'pending',
                error_message TEXT,

                created_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP
            )
        """))
        conn.commit()
        print("   ✓ persona_generations table created")
        print()

        # Step 2: Create personas table
        print("2. Creating personas table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS personas (
                id SERIAL PRIMARY KEY,
                generation_id INTEGER NOT NULL REFERENCES persona_generations(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                brand_id INTEGER NOT NULL REFERENCES brand_info(id),

                -- Persona type
                persona_type VARCHAR(20) NOT NULL,  -- 'patient' or 'hcp'
                persona_number INTEGER NOT NULL,    -- 1-4

                -- Patient Persona Fields - Demographics
                name VARCHAR(200),
                age VARCHAR(50),
                location VARCHAR(200),
                family_status VARCHAR(200),
                occupation VARCHAR(200),
                tech_savviness VARCHAR(100),

                -- Clinical Profile
                clinical_scenario TEXT,
                recent_diagnosis VARCHAR(300),
                mindset TEXT,

                -- Goals & Fears
                goals TEXT,
                fears TEXT,

                -- Information Journey
                information_channels TEXT,
                key_doctor_question TEXT,

                -- Marketing/Messaging Cues
                marketing_message TEXT,
                marketing_tone VARCHAR(200),
                call_to_action TEXT,

                -- HCP Persona Fields
                specialty VARCHAR(200),
                years_experience VARCHAR(50),
                practice_setting VARCHAR(200),
                patient_volume VARCHAR(100),
                disease_focus VARCHAR(200),
                prescribing_preferences TEXT,
                information_sources TEXT,
                clinical_challenges TEXT,

                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ personas table created")
        print()

        # Step 3: Add indexes for performance
        print("3. Adding indexes...")

        # persona_generations indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_gen_user_id
            ON persona_generations(user_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_gen_brand_id
            ON persona_generations(brand_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_gen_user_brand
            ON persona_generations(user_id, brand_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_gen_status
            ON persona_generations(status, created_at)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_gen_created_at
            ON persona_generations(created_at)
        """))

        # personas indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_generation_id
            ON personas(generation_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_user_id
            ON personas(user_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_brand_id
            ON personas(brand_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_generation
            ON personas(generation_id, persona_type)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_persona_user_brand
            ON personas(user_id, brand_id)
        """))

        conn.commit()
        print("   ✓ All indexes created")
        print()

        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - persona_generations table created")
        print("  - personas table created")
        print("  - 10 performance indexes added")
        print()
        print("Next steps:")
        print("  1. Add Heads API routes to backend")
        print("  2. Copy Heads persona generation services")
        print("  3. Create Heads frontend pages")
        print("  4. Add ProductSwitcher component to navigation")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
