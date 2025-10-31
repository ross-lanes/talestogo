-- Migration: 000_add_invitation_columns.sql
-- Purpose: Add missing invitation_token and invitation_expires_at columns to users table
-- Created: 2025-10-31
-- Description: The models.py file defines these columns but they're missing from the database.
--              This migration adds them to sync the schema.

BEGIN TRANSACTION;

-- Add invitation_token column
ALTER TABLE users ADD COLUMN invitation_token VARCHAR(500);

-- Add invitation_expires_at column
ALTER TABLE users ADD COLUMN invitation_expires_at DATETIME;

-- Create index on invitation_token for faster lookups
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_invitation_token ON users(invitation_token);

COMMIT;

-- Verification:
-- PRAGMA table_info(users);
-- Should show invitation_token and invitation_expires_at columns
