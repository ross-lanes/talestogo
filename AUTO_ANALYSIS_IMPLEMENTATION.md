# Automatic Analysis After Collection - Implementation Guide

## Overview
Implemented automatic analysis triggering that runs immediately after data collection completes, for both manual and scheduled tasks. This ensures a seamless one-button workflow where users don't need to manually trigger analysis after collecting data.

## Features

### 1. Manual Collection with Auto-Analysis
When a user clicks "Run Data Collection" in the UI:
1. **Collection Phase** - Data is collected from all AI platforms (ChatGPT, Claude, Gemini, Perplexity)
2. **Automatic Analysis Phase** - Once collection completes successfully, analysis automatically begins
3. **Email Notifications** - User receives two emails: one when collection completes, one when analysis completes
4. **Task Status Tracking** - Both phases show up in the task status banner with real-time progress

### 2. Scheduled Monthly Tasks
Automated monthly data collection and analysis:
1. **Scheduled Collection** - Runs at configured time (e.g., 1st of every month)
2. **Automatic Analysis** - Immediately follows collection completion
3. **Email Summary** - Single email notification with results from both collection and analysis
4. **Next Run Scheduling** - Automatically schedules the next monthly run

## Implementation Details

### Backend Changes

#### 1. Collection Endpoint (`app/main.py`)
**Endpoint:** `POST /tasks/run-collection/`

**Previous Behavior:**
- Triggered data collection only
- User had to manually trigger analysis afterward

**New Behavior:**
- Starts collection in background thread
- Waits for collection to complete
- Automatically triggers analysis with newly collected responses
- Sends email notifications for both collection and analysis
- Returns immediately to user with task ID

**Key Code Pattern:**
```python
def run_collection_then_analysis():
    # Phase 1: Run Collection
    collection_process = subprocess.Popen([collection_script, ...])
    stdout, stderr = collection_process.communicate(timeout=3600)

    if collection_process.returncode != 0:
        # Mark collection as failed and send email
        send_task_completion_email(status='failed', ...)
        return

    # Mark collection as completed and send email
    send_task_completion_email(status='completed', ...)

    # Phase 2: Run Analysis Automatically
    analysis_process = subprocess.Popen([analysis_script, ...])
    stdout, stderr = analysis_process.communicate(timeout=3600)

    # Mark analysis as completed/failed and send email
    send_task_completion_email(status='completed/failed', ...)
```

#### 2. Scheduler (`app/scheduler.py`)
**Function:** `execute_scheduled_task(schedule_id)`

**Behavior** (already implemented):
- Runs collection with `wait_for_task_completion()`
- When collection completes successfully, automatically triggers analysis
- Sends consolidated email notification
- Updates next run time

**No changes needed** - scheduler already had auto-analysis working correctly.

#### 3. Collection Script (`collect_responses.py`)
**Changes:**
- Added `batch_id` and `total_responses` to return stats dictionary
- This allows the caller to track which batch was created

### Email Notifications

#### Collection Complete Email
```
Subject: TALES Data Collection Complete - [Brand Name]

Your data collection has completed successfully!

Brand: [Brand Name]
Responses Collected: [X]
Started: [timestamp]
Completed: [timestamp]

Analysis will start automatically...

--
TALES - AI Reputation Intelligence
```

#### Analysis Complete Email
```
Subject: TALES Analysis Complete - [Brand Name]

Your data analysis has completed successfully!

Brand: [Brand Name]
Responses Analyzed: [X]
Started: [timestamp]
Completed: [timestamp]

View your results: https://tales.yourlab.gov/analytics

--
TALES - AI Reputation Intelligence
```

#### Failure Email
```
Subject: TALES Alert: Task Failed - [Brand Name]

Your [collection/analysis] encountered an error.

Brand: [Brand Name]
Status: FAILED
Error: [error message]

Please log in to review: https://tales.yourlab.gov/collect-analyze

--
TALES - AI Reputation Intelligence
```

### Task Status Banner

The task status banner shows both phases:

**During Collection:**
```
┌─────────────────────────────────┐
│ Data Collection                  │
│ ● Running - 45% complete         │
│ 18 of 40 items processed        │
│ Collecting from ChatGPT...      │
└─────────────────────────────────┘
```

**After Collection, During Analysis:**
```
┌─────────────────────────────────┐
│ Data Collection                  │
│ ✓ Completed - 100%               │
│ 40 of 40 items processed        │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Data Analysis                    │
│ ● Running - 30% complete         │
│ 12 of 40 items processed        │
│ Analyzing response 12/40...     │
└─────────────────────────────────┘
```

## User Experience

### Manual Workflow
1. User navigates to "Collect & Analyze" page
2. User clicks "Run Data Collection" button
3. Collection starts - banner appears showing progress
4. Collection completes - user receives email notification
5. Analysis starts automatically - banner updates to show analysis progress
6. Analysis completes - user receives second email notification
7. User can view results in Analytics section

### Scheduled Workflow
1. Admin sets up monthly schedule (e.g., "1st of every month at 9 AM")
2. System automatically runs collection at scheduled time
3. Collection completes
4. Analysis automatically begins
5. Analysis completes
6. User receives email with summary of both collection and analysis
7. Next run is automatically scheduled

## Configuration

### Email Settings (Environment Variables)
Add these to your `.env` file:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=TALES
FRONTEND_URL=https://tales.yourlab.gov
```

### Timeout Settings
Both collection and analysis have 1-hour timeouts. To adjust:

**In `app/main.py`:**
```python
# Collection timeout (default: 3600 seconds = 1 hour)
stdout, stderr = process.communicate(timeout=3600)

# Analysis timeout (default: 3600 seconds = 1 hour)
stdout, stderr = analysis_process.communicate(timeout=3600)
```

**In `app/scheduler.py`:**
```python
# Task completion polling timeout (default: 3600 seconds = 1 hour)
await wait_for_task_completion(
    schedule.user_id,
    'collection',
    db,
    timeout=3600
)
```

## Error Handling

### Collection Fails
- Collection task marked as "failed"
- Error email sent to user
- Analysis does NOT run (prevents analyzing incomplete data)
- User can manually retry collection from UI

### Collection Succeeds, Analysis Fails
- Collection task marked as "completed"
- Analysis task marked as "failed"
- Two emails sent: one success (collection), one failure (analysis)
- User can manually re-run analysis only from UI

### Timeout Errors
- Task marked as "failed" with timeout error message
- Email notification sent
- Process is killed to prevent hanging

## Testing

### Test Manual Collection + Analysis
1. Log in to TALES
2. Go to "Collect & Analyze" page
3. Click "Run Data Collection"
4. Observe task status banner showing collection progress
5. Wait for collection to complete (~5-10 minutes depending on query count)
6. Observe banner automatically showing analysis progress
7. Wait for analysis to complete (~10-20 minutes depending on response count)
8. Check email for two notification emails
9. Verify analytics data appears in Dashboard

### Test Scheduled Collection + Analysis
1. Log in as admin
2. Go to "Collect & Analyze" page, "Schedule" tab
3. Create a schedule (or edit existing)
4. Set next run time to 1 minute in the future
5. Wait for scheduled time
6. Check "Schedule History" to see both collection and analysis ran
7. Check email for notification
8. Verify analytics data updated

### Test Failure Scenarios
**Collection Failure:**
1. Temporarily remove API keys from `.env` (e.g., comment out `OPENAI_API_KEY`)
2. Run collection
3. Observe collection fails
4. Verify analysis does NOT start
5. Check email for failure notification
6. Restore API keys

**Analysis Failure:**
1. Temporarily remove `PERPLEXITY_API_KEY` from `.env`
2. Run collection (will succeed with other platforms)
3. Observe analysis starts but fails
4. Check emails: one success (collection), one failure (analysis)

## Files Modified

### Backend
- `app/main.py` - Updated `/tasks/run-collection/` endpoint
- `collect_responses.py` - Added batch_id to return stats
- `app/services/email_notifications.py` - Email notification service (already existed)

### Scheduler
- `app/scheduler.py` - No changes needed (already had auto-analysis)

### Frontend
- No changes needed - existing UI works with new backend behavior

## Notes

- The scheduler (`app/scheduler.py`) already had automatic analysis implemented - no changes were needed there
- Manual collection now matches the behavior of scheduled collection
- Both collection and analysis send separate email notifications for better transparency
- Email sending is non-blocking and won't crash the app if SMTP is not configured
- Task status tracking uses existing `TaskStatus` model - no database schema changes needed
- All timeouts are set to 1 hour to handle large datasets

## Troubleshooting

### Emails Not Sending
Check SMTP configuration in `.env` file. The app will continue working even if email fails.

### Analysis Not Starting After Collection
Check server logs for errors. The analysis should start within 1-2 seconds of collection completing.

### Tasks Timing Out
Increase timeout values in `app/main.py` and `app/scheduler.py` for larger datasets.

### Background Threads Not Working
Ensure threading is enabled in your Python environment. Background threads are daemon threads and will not block server shutdown.
