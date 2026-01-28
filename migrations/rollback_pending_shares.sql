-- Rollback Migration: Remove pending shares columns
-- This SQL script removes the pending_email and is_pending columns from brand_shares table

-- Step 1: Delete any pending shares (where user_id is NULL)
DELETE FROM brand_shares WHERE user_id IS NULL;

-- Step 2: Make user_id NOT NULL again
ALTER TABLE brand_shares ALTER COLUMN user_id SET NOT NULL;

-- Step 3: Drop indexes
DROP INDEX IF EXISTS ix_brand_shares_pending_email;
DROP INDEX IF EXISTS ix_brand_shares_is_pending;

-- Step 4: Drop columns
ALTER TABLE brand_shares DROP COLUMN IF EXISTS pending_email;
ALTER TABLE brand_shares DROP COLUMN IF EXISTS is_pending;

-- Done!
SELECT 'Rollback completed successfully!' as message;
