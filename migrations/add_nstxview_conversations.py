#!/usr/bin/env python3
"""
Migration: Add NSTXView Conversation Memory tables

This migration:
1. Creates nstx_conversations table for saved conversation metadata
2. Creates nstx_conversation_messages table for individual messages
3. Creates indexes for performance
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """Run the NSTXView conversation tables migration"""

    with engine.connect() as conn:
        print("Starting NSTXView conversation tables migration...")
        print()

        # Step 1: Create nstx_conversations table
        print("1. Creating nstx_conversations table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nstx_conversations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                -- Conversation metadata
                title VARCHAR(255) NOT NULL,
                summary TEXT,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ nstx_conversations table created")
        print()

        # Step 2: Create nstx_conversation_messages table
        print("2. Creating nstx_conversation_messages table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nstx_conversation_messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER NOT NULL REFERENCES nstx_conversations(id) ON DELETE CASCADE,

                -- Message content
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,

                -- Ordering
                sequence INTEGER NOT NULL,

                -- Timestamp
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        print("   ✓ nstx_conversation_messages table created")
        print()

        # Step 3: Add indexes for performance
        print("3. Adding indexes...")

        # nstx_conversations indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_conv_user_created
            ON nstx_conversations(user_id, created_at DESC)
        """))

        # nstx_conversation_messages indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_nstx_msg_conv_seq
            ON nstx_conversation_messages(conversation_id, sequence)
        """))

        conn.commit()
        print("   ✓ All indexes created")
        print()

        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  - nstx_conversations table created")
        print("  - nstx_conversation_messages table created")
        print("  - 2 performance indexes added")
        print()
        print("Limits configured in app/models.py:")
        print("  - MAX_SAVED_CONVERSATIONS_PER_USER = 20")
        print("  - MAX_MESSAGES_PER_CONVERSATION = 100")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
