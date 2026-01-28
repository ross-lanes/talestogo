-- Rollback: Remove Scheduling System Tables
-- Date: 2025-11-04
-- Description: Removes scheduled_tasks and scheduled_task_history tables

-- Drop indexes first
DROP INDEX IF EXISTS idx_scheduled_history_brand;
DROP INDEX IF EXISTS idx_scheduled_history_user;
DROP INDEX IF EXISTS idx_scheduled_history_started;
DROP INDEX IF EXISTS idx_scheduled_history_task;
DROP INDEX IF EXISTS idx_scheduled_tasks_brand;
DROP INDEX IF EXISTS idx_scheduled_tasks_user;
DROP INDEX IF EXISTS idx_scheduled_tasks_next_run;

-- Drop tables (history first due to foreign key)
DROP TABLE IF EXISTS scheduled_task_history;
DROP TABLE IF EXISTS scheduled_tasks;
