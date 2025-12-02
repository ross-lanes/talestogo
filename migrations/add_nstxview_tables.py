#!/usr/bin/env python3
"""
Migration: Add NSTXView (NSTX-U Research Analysis) tables

This migration:
1. Creates nstx_papers table for paper metadata and extracted text
2. Creates nstx_shots table for shot numbers and characteristics
3. Creates nstx_parameters table for plasma parameters
4. Creates nstx_phenomena table for observed phenomena
5. Creates nstx_paper_chunks table for vector search
6. Creates nstx_processing_tasks table for background processing
7. Creates indexes for performance
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """Run the NSTXView tables migration"""

    with engine.connect() as conn:
        print("Starting NSTXView tables migration...")
        print()

        # Step 1: Create nstx_papers table
        print("1. Creating nstx_papers table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nstx_papers (
                id SERIAL PRIMARY KEY,

                -- Source tracking
                drive_file_id VARCHAR(255) UNIQUE,
                drive_folder_path VARCHAR(500),
                filename VARCHAR(500),
                file_hash VARCHAR(64),

                -- Paper metadata
                title VARCHAR(1000),
                authors JSONB,
                abstract TEXT,
                doi VARCHAR(255),
                journal VARCHAR(255),
                publication_date DATE,

                -- Extracted content
                extracted_text TEXT,
                page_count INTEGER,

                -- Paper classification
                experiment_type VARCHAR(100),
                key_findings JSONB,

                -- Processing status
                status VARCHAR(50) DEFAULT 'pending',
                processed_at TIMESTAMP,
                extraction_version VARCHAR(20),
                error_message TEXT,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ nstx_papers table created")
        print()

        # Step 2: Create nstx_shots table
        print("2. Creating nstx_shots table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nstx_shots (
                id SERIAL PRIMARY KEY,
                paper_id INTEGER NOT NULL REFERENCES nstx_papers(id) ON DELETE CASCADE,

                -- Shot identification (6-digit number starting with 1: 100000-199999)
                shot_number INTEGER NOT NULL,

                -- Context in paper
                role VARCHAR(50),
                context TEXT,
                page_number INTEGER,

                -- Extracted characteristics
                characteristics JSONB,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ nstx_shots table created")
        print()

        # Step 3: Create nstx_parameters table
        print("3. Creating nstx_parameters table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nstx_parameters (
                id SERIAL PRIMARY KEY,
                paper_id INTEGER NOT NULL REFERENCES nstx_papers(id) ON DELETE CASCADE,
                shot_id INTEGER REFERENCES nstx_shots(id) ON DELETE SET NULL,

                -- Parameter identification
                parameter_name VARCHAR(100) NOT NULL,
                parameter_category VARCHAR(100),

                -- Value with units
                value FLOAT,
                value_min FLOAT,
                value_max FLOAT,
                unit VARCHAR(50),
                normalized_value FLOAT,
                normalized_unit VARCHAR(50),
                uncertainty FLOAT,

                -- Context
                context TEXT,
                page_number INTEGER,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ nstx_parameters table created")
        print()

        # Step 4: Create nstx_phenomena table
        print("4. Creating nstx_phenomena table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nstx_phenomena (
                id SERIAL PRIMARY KEY,
                paper_id INTEGER NOT NULL REFERENCES nstx_papers(id) ON DELETE CASCADE,
                shot_id INTEGER REFERENCES nstx_shots(id) ON DELETE SET NULL,

                -- Phenomenon classification
                phenomenon_type VARCHAR(100) NOT NULL,
                phenomenon_category VARCHAR(100),

                -- Details
                description TEXT,
                is_primary_focus BOOLEAN DEFAULT FALSE,

                -- Context
                context TEXT,
                page_number INTEGER,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ nstx_phenomena table created")
        print()

        # Step 5: Create nstx_paper_chunks table
        print("5. Creating nstx_paper_chunks table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nstx_paper_chunks (
                id SERIAL PRIMARY KEY,
                paper_id INTEGER NOT NULL REFERENCES nstx_papers(id) ON DELETE CASCADE,

                -- Chunk content
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                section_name VARCHAR(100),

                -- Vector store reference (ChromaDB)
                chromadb_id VARCHAR(255) UNIQUE,

                -- Metadata
                page_start INTEGER,
                page_end INTEGER,
                word_count INTEGER,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ nstx_paper_chunks table created")
        print()

        # Step 6: Create nstx_processing_tasks table
        print("6. Creating nstx_processing_tasks table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nstx_processing_tasks (
                id SERIAL PRIMARY KEY,

                -- Task identification
                task_type VARCHAR(50) NOT NULL,
                paper_id INTEGER REFERENCES nstx_papers(id) ON DELETE SET NULL,

                -- Status
                status VARCHAR(50) DEFAULT 'pending',
                progress INTEGER DEFAULT 0,

                -- Details
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                result JSONB,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ nstx_processing_tasks table created")
        print()

        # Step 7: Add indexes for performance
        print("7. Adding indexes...")

        # nstx_papers indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_papers_status
            ON nstx_papers(status)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_papers_drive_file_id
            ON nstx_papers(drive_file_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_papers_doi
            ON nstx_papers(doi)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_papers_experiment_type
            ON nstx_papers(experiment_type)
        """))

        # nstx_shots indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_shots_paper_id
            ON nstx_shots(paper_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_shots_shot_number
            ON nstx_shots(shot_number)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_shots_role
            ON nstx_shots(role)
        """))

        # nstx_parameters indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_parameters_paper_id
            ON nstx_parameters(paper_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_parameters_shot_id
            ON nstx_parameters(shot_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_parameters_name
            ON nstx_parameters(parameter_name)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_parameters_category
            ON nstx_parameters(parameter_category)
        """))

        # nstx_phenomena indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_phenomena_paper_id
            ON nstx_phenomena(paper_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_phenomena_shot_id
            ON nstx_phenomena(shot_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_phenomena_type
            ON nstx_phenomena(phenomenon_type)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_phenomena_category
            ON nstx_phenomena(phenomenon_category)
        """))

        # nstx_paper_chunks indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_chunks_paper_id
            ON nstx_paper_chunks(paper_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_chunks_chromadb_id
            ON nstx_paper_chunks(chromadb_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_chunks_section
            ON nstx_paper_chunks(section_name)
        """))

        # nstx_processing_tasks indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_tasks_status
            ON nstx_processing_tasks(status)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_tasks_type
            ON nstx_processing_tasks(task_type)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_tasks_paper_id
            ON nstx_processing_tasks(paper_id)
        """))

        conn.commit()
        print("   ✓ All indexes created")
        print()

        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - nstx_papers table created")
        print("  - nstx_shots table created")
        print("  - nstx_parameters table created")
        print("  - nstx_phenomena table created")
        print("  - nstx_paper_chunks table created")
        print("  - nstx_processing_tasks table created")
        print("  - 18 performance indexes added")
        print()
        print("Next steps:")
        print("  1. Install dependencies: pip install pymupdf chromadb google-api-python-client")
        print("  2. Set up ChromaDB service")
        print("  3. Configure Google Drive API credentials")
        print("  4. Add nstxview_white.png to frontend/public/")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
