-- Migration: 002_add_not_null_constraints.sql
-- Purpose: Add NOT NULL constraints to user_id columns to prevent future orphaned records
-- Created: 2025-10-31
-- Description: This migration adds NOT NULL constraints to all user_id columns in data tables.
--              This ensures that all future records MUST have a user_id, preventing data leakage.
--
-- PREREQUISITE: Run 001_cleanup_orphaned_data.sql FIRST to remove existing NULL values
--
-- IMPORTANT: BACKUP YOUR DATABASE BEFORE RUNNING THIS MIGRATION!
-- Run: cp tales.db tales.db.backup_$(date +%Y%m%d_%H%M%S)

-- SQLite Note: SQLite doesn't support ALTER COLUMN directly, so we need to:
-- 1. Create a new table with the correct constraints
-- 2. Copy data from old table to new table
-- 3. Drop old table
-- 4. Rename new table to old name
-- 5. Recreate indexes

-- This is a complex migration, so we'll do it table by table.

BEGIN TRANSACTION;

-- ============================================================================
-- QUERIES TABLE
-- ============================================================================

-- Create new table with NOT NULL constraint on user_id
CREATE TABLE queries_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER,
    query_id VARCHAR(10) NOT NULL,
    query_text TEXT NOT NULL,
    category VARCHAR(100),
    priority VARCHAR(20),
    target_outcome TEXT,
    active BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (brand_id) REFERENCES brand_info(id)
);

-- Copy data from old table
INSERT INTO queries_new SELECT * FROM queries;

-- Drop old table
DROP TABLE queries;

-- Rename new table
ALTER TABLE queries_new RENAME TO queries;

-- Recreate indexes
CREATE INDEX ix_queries_id ON queries(id);
CREATE INDEX ix_queries_user_id ON queries(user_id);
CREATE INDEX ix_queries_brand_id ON queries(brand_id);
CREATE INDEX ix_queries_query_id ON queries(query_id);

-- ============================================================================
-- RESPONSES TABLE
-- ============================================================================

CREATE TABLE responses_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER,
    query_id VARCHAR(10) NOT NULL,
    query_text TEXT,
    platform VARCHAR(20) NOT NULL,
    response_text TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    brand_mentioned VARCHAR(10),
    brand_position VARCHAR(20),
    sentiment VARCHAR(20),
    descriptors TEXT,
    competitors TEXT,
    sources TEXT,
    campaign_period VARCHAR(100),
    notes TEXT,
    analyzed_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (brand_id) REFERENCES brand_info(id)
);

INSERT INTO responses_new SELECT * FROM responses;
DROP TABLE responses;
ALTER TABLE responses_new RENAME TO responses;

CREATE INDEX ix_responses_id ON responses(id);
CREATE INDEX ix_responses_user_id ON responses(user_id);
CREATE INDEX ix_responses_brand_id ON responses(brand_id);
CREATE INDEX ix_responses_query_id ON responses(query_id);
CREATE INDEX ix_responses_platform ON responses(platform);
CREATE INDEX ix_responses_timestamp ON responses(timestamp);
CREATE INDEX ix_responses_analyzed_at ON responses(analyzed_at);

-- ============================================================================
-- COMPETITORS TABLE
-- ============================================================================

CREATE TABLE competitors_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER,
    organization VARCHAR(200) NOT NULL,
    type VARCHAR(100),
    focus_area TEXT,
    track BOOLEAN DEFAULT 1,
    key_descriptors TEXT,
    website VARCHAR(500),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (brand_id) REFERENCES brand_info(id)
);

INSERT INTO competitors_new SELECT * FROM competitors;
DROP TABLE competitors;
ALTER TABLE competitors_new RENAME TO competitors;

CREATE INDEX ix_competitors_id ON competitors(id);
CREATE INDEX ix_competitors_user_id ON competitors(user_id);
CREATE INDEX ix_competitors_brand_id ON competitors(brand_id);
CREATE INDEX ix_competitors_organization ON competitors(organization);

-- ============================================================================
-- TARGET_DESCRIPTORS TABLE
-- ============================================================================

CREATE TABLE target_descriptors_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER,
    descriptor VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    is_target BOOLEAN DEFAULT 1,
    current_ownership VARCHAR(200),
    priority VARCHAR(20),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (brand_id) REFERENCES brand_info(id)
);

INSERT INTO target_descriptors_new SELECT * FROM target_descriptors;
DROP TABLE target_descriptors;
ALTER TABLE target_descriptors_new RENAME TO target_descriptors;

CREATE INDEX ix_target_descriptors_id ON target_descriptors(id);
CREATE INDEX ix_target_descriptors_user_id ON target_descriptors(user_id);
CREATE INDEX ix_target_descriptors_brand_id ON target_descriptors(brand_id);
CREATE INDEX ix_target_descriptors_descriptor ON target_descriptors(descriptor);

-- ============================================================================
-- CAMPAIGNS TABLE
-- ============================================================================

CREATE TABLE campaigns_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER,
    campaign_name VARCHAR(200) NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50),
    target_narrative TEXT,
    key_messages TEXT,
    success_metrics TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (brand_id) REFERENCES brand_info(id)
);

INSERT INTO campaigns_new SELECT * FROM campaigns;
DROP TABLE campaigns;
ALTER TABLE campaigns_new RENAME TO campaigns;

CREATE INDEX ix_campaigns_id ON campaigns(id);
CREATE INDEX ix_campaigns_user_id ON campaigns(user_id);
CREATE INDEX ix_campaigns_brand_id ON campaigns(brand_id);
CREATE INDEX ix_campaigns_campaign_name ON campaigns(campaign_name);

-- ============================================================================
-- CITED_SOURCES TABLE
-- ============================================================================

CREATE TABLE cited_sources_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER,
    source_name VARCHAR(200) NOT NULL,
    source_type VARCHAR(100),
    authority_level VARCHAR(20),
    brand_coverage TEXT,
    last_cited DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (brand_id) REFERENCES brand_info(id)
);

INSERT INTO cited_sources_new SELECT * FROM cited_sources;
DROP TABLE cited_sources;
ALTER TABLE cited_sources_new RENAME TO cited_sources;

CREATE INDEX ix_cited_sources_id ON cited_sources(id);
CREATE INDEX ix_cited_sources_user_id ON cited_sources(user_id);
CREATE INDEX ix_cited_sources_brand_id ON cited_sources(brand_id);
CREATE INDEX ix_cited_sources_source_name ON cited_sources(source_name);

-- ============================================================================
-- REPORTS TABLE
-- ============================================================================

CREATE TABLE reports_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER,
    title VARCHAR(200) NOT NULL,
    report_content TEXT NOT NULL,
    start_date DATETIME,
    end_date DATETIME,
    total_responses INTEGER DEFAULT 0,
    mention_rate FLOAT,
    google_doc_url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (brand_id) REFERENCES brand_info(id)
);

INSERT INTO reports_new SELECT * FROM reports;
DROP TABLE reports;
ALTER TABLE reports_new RENAME TO reports;

CREATE INDEX ix_reports_id ON reports(id);
CREATE INDEX ix_reports_user_id ON reports(user_id);
CREATE INDEX ix_reports_brand_id ON reports(brand_id);
CREATE INDEX ix_reports_created_at ON reports(created_at);

-- ============================================================================
-- TASK_STATUS TABLE
-- ============================================================================

CREATE TABLE task_status_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    brand_id INTEGER,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    progress INTEGER DEFAULT 0,
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    message TEXT,
    error_message TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (brand_id) REFERENCES brand_info(id)
);

INSERT INTO task_status_new SELECT * FROM task_status;
DROP TABLE task_status;
ALTER TABLE task_status_new RENAME TO task_status;

CREATE INDEX ix_task_status_id ON task_status(id);
CREATE INDEX ix_task_status_user_id ON task_status(user_id);
CREATE INDEX ix_task_status_brand_id ON task_status(brand_id);
CREATE INDEX ix_task_status_status ON task_status(status);
CREATE INDEX ix_task_status_started_at ON task_status(started_at);

-- ============================================================================
-- TRENDS TABLE
-- ============================================================================

CREATE TABLE trends_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    period VARCHAR(20) NOT NULL,
    grouping VARCHAR(10) NOT NULL,
    mention_rate FLOAT,
    share_of_voice FLOAT,
    avg_visibility_score FLOAT,
    sentiment_rate FLOAT,
    descriptor_match_rate FLOAT,
    response_count INTEGER,
    pppl_mention_count INTEGER,
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO trends_new SELECT * FROM trends;
DROP TABLE trends;
ALTER TABLE trends_new RENAME TO trends;

CREATE INDEX ix_trends_id ON trends(id);
CREATE INDEX ix_trends_user_id ON trends(user_id);
CREATE INDEX ix_trends_period ON trends(period);
CREATE INDEX ix_trends_grouping ON trends(grouping);

-- ============================================================================
-- ANALYSES TABLE
-- ============================================================================

CREATE TABLE analyses_new (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    executive_summary TEXT,
    recommendations TEXT,
    full_analysis_text TEXT,
    report_url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO analyses_new SELECT * FROM analyses;
DROP TABLE analyses;
ALTER TABLE analyses_new RENAME TO analyses;

CREATE INDEX ix_analyses_id ON analyses(id);
CREATE INDEX ix_analyses_user_id ON analyses(user_id);

COMMIT;

-- Verify the constraints are in place
-- Run these to check the schema:

-- PRAGMA table_info(queries);
-- PRAGMA table_info(responses);
-- PRAGMA table_info(competitors);
-- PRAGMA table_info(target_descriptors);
-- PRAGMA table_info(campaigns);
-- PRAGMA table_info(cited_sources);
-- PRAGMA table_info(reports);
-- PRAGMA table_info(task_status);
-- PRAGMA table_info(trends);
-- PRAGMA table_info(analyses);

-- Look for "notnull" column - should be 1 for user_id

-- Migration complete!
