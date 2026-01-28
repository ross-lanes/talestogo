-- Migration: Add Scheduling System Tables
-- Date: 2025-11-04
-- Description: Adds scheduled_tasks and scheduled_task_history tables for automated monthly data collection

-- Create scheduled_tasks table
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    brand_id INTEGER NOT NULL REFERENCES brand_info(id) ON DELETE CASCADE,

    -- Schedule configuration
    schedule_type VARCHAR(20) NOT NULL CHECK (schedule_type IN ('first_day', 'middle', 'last_day')),
    is_enabled BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Execution tracking
    last_run_at TIMESTAMP NULL,
    next_run_at TIMESTAMP NULL,
    last_batch_id INTEGER NULL REFERENCES collection_batches(id),

    -- Notification preferences
    send_email_notification BOOLEAN DEFAULT TRUE,
    notification_email VARCHAR(255) NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: one schedule per brand
    UNIQUE(brand_id, user_id)
);

-- Create index for scheduler queries
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run
ON scheduled_tasks(next_run_at, is_enabled);

-- Create index for user lookups
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_user
ON scheduled_tasks(user_id);

-- Create index for brand lookups
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_brand
ON scheduled_tasks(brand_id);


-- Create scheduled_task_history table
CREATE TABLE IF NOT EXISTS scheduled_task_history (
    id SERIAL PRIMARY KEY,
    scheduled_task_id INTEGER NOT NULL REFERENCES scheduled_tasks(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    brand_id INTEGER NOT NULL REFERENCES brand_info(id),

    -- Execution details
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'partial', 'running')),

    -- Results
    batch_id INTEGER NULL REFERENCES collection_batches(id),
    collection_responses INTEGER DEFAULT 0,
    analysis_responses INTEGER DEFAULT 0,
    error_message TEXT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for history queries
CREATE INDEX IF NOT EXISTS idx_scheduled_history_task
ON scheduled_task_history(scheduled_task_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_scheduled_history_started
ON scheduled_task_history(started_at);

CREATE INDEX IF NOT EXISTS idx_scheduled_history_user
ON scheduled_task_history(user_id);

CREATE INDEX IF NOT EXISTS idx_scheduled_history_brand
ON scheduled_task_history(brand_id);


-- Add comments for documentation
COMMENT ON TABLE scheduled_tasks IS 'Stores configuration for automated monthly data collection schedules';
COMMENT ON TABLE scheduled_task_history IS 'Audit trail of scheduled task executions';

COMMENT ON COLUMN scheduled_tasks.schedule_type IS 'When to run: first_day (1st), middle (15th), or last_day (last day of month)';
COMMENT ON COLUMN scheduled_tasks.next_run_at IS 'Next scheduled execution time (UTC)';
COMMENT ON COLUMN scheduled_task_history.status IS 'Execution result: success, failed, partial, or running';
