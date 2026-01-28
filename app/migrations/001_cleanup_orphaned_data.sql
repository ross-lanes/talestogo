-- Migration: 001_cleanup_orphaned_data.sql
-- Purpose: Remove orphaned records without user_id (data leakage fix)
-- Created: 2025-10-31
-- Description: This migration removes all records from data tables that don't have
--              a proper user_id association. These orphaned records were likely created
--              by the old seed_db.py script and cause data leakage where new users
--              see PPPL-specific data.

-- IMPORTANT: BACKUP YOUR DATABASE BEFORE RUNNING THIS MIGRATION!
-- Run: cp tales.db tales.db.backup_$(date +%Y%m%d_%H%M%S)

-- Step 1: Identify orphaned records (for verification)
-- Uncomment these to see what will be deleted:

-- SELECT COUNT(*) as orphaned_queries FROM queries WHERE user_id IS NULL;
-- SELECT COUNT(*) as orphaned_responses FROM responses WHERE user_id IS NULL;
-- SELECT COUNT(*) as orphaned_competitors FROM competitors WHERE user_id IS NULL;
-- SELECT COUNT(*) as orphaned_descriptors FROM target_descriptors WHERE user_id IS NULL;
-- SELECT COUNT(*) as orphaned_campaigns FROM campaigns WHERE user_id IS NULL;
-- SELECT COUNT(*) as orphaned_sources FROM cited_sources WHERE user_id IS NULL;
-- SELECT COUNT(*) as orphaned_reports FROM reports WHERE user_id IS NULL;
-- SELECT COUNT(*) as orphaned_task_status FROM task_status WHERE user_id IS NULL;

-- SELECT * FROM queries WHERE user_id IS NULL LIMIT 5;
-- SELECT * FROM target_descriptors WHERE user_id IS NULL LIMIT 5;
-- SELECT * FROM competitors WHERE user_id IS NULL LIMIT 5;

-- Step 2: Delete orphaned records
-- These records have no user_id and should not exist in a multi-tenant system

BEGIN TRANSACTION;

-- Delete orphaned task status records
DELETE FROM task_status WHERE user_id IS NULL;

-- Delete orphaned responses (must be done before queries due to query_id reference)
DELETE FROM responses WHERE user_id IS NULL;

-- Delete orphaned queries
DELETE FROM queries WHERE user_id IS NULL;

-- Delete orphaned competitors
DELETE FROM competitors WHERE user_id IS NULL;

-- Delete orphaned target descriptors
DELETE FROM target_descriptors WHERE user_id IS NULL;

-- Delete orphaned campaigns
DELETE FROM campaigns WHERE user_id IS NULL;

-- Delete orphaned cited sources
DELETE FROM cited_sources WHERE user_id IS NULL;

-- Delete orphaned reports
DELETE FROM reports WHERE user_id IS NULL;

-- Delete orphaned trends (trends table also has user_id)
DELETE FROM trends WHERE user_id IS NULL;

-- Delete orphaned analyses
DELETE FROM analyses WHERE user_id IS NULL;

COMMIT;

-- Step 3: Verify cleanup
-- Run these after the migration to confirm all orphaned data is gone:

-- SELECT COUNT(*) FROM queries WHERE user_id IS NULL;
-- SELECT COUNT(*) FROM responses WHERE user_id IS NULL;
-- SELECT COUNT(*) FROM competitors WHERE user_id IS NULL;
-- SELECT COUNT(*) FROM target_descriptors WHERE user_id IS NULL;
-- SELECT COUNT(*) FROM campaigns WHERE user_id IS NULL;
-- SELECT COUNT(*) FROM cited_sources WHERE user_id IS NULL;
-- SELECT COUNT(*) FROM reports WHERE user_id IS NULL;
-- SELECT COUNT(*) FROM task_status WHERE user_id IS NULL;

-- All counts should be 0

-- Migration complete!
