-- Migration script to add microsoft_id column to users table
-- Run this in Render's PostgreSQL database shell

-- Check if column exists (this will show error if it doesn't exist, which is fine)
SELECT column_name FROM information_schema.columns
WHERE table_name='users' AND column_name='microsoft_id';

-- Add the column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='microsoft_id'
    ) THEN
        ALTER TABLE users ADD COLUMN microsoft_id VARCHAR(255) UNIQUE;
        CREATE INDEX ix_users_microsoft_id ON users(microsoft_id);
        RAISE NOTICE 'Added microsoft_id column and index';
    ELSE
        RAISE NOTICE 'Column microsoft_id already exists';
    END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name='users' AND column_name='microsoft_id';
