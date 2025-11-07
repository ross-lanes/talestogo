# Task Status Banner Implementation

## Overview
Implemented a global task status monitoring system that shows users when data collection or analysis tasks are running, even when they navigate away and return to the site.

## Features

### 1. Global Task Status Banner
- **Fixed position** in top-right corner (below app bar)
- Appears automatically when tasks are running
- **Persists across all pages** within the brand
- Shows up to multiple concurrent tasks
- Auto-refreshes every 5 seconds

### 2. Task Information Displayed
- **Task type** (Data Collection, Data Analysis, Report Generation)
- **Status** (Running, Completed, Failed)
- **Progress** (0-100% with animated progress bar)
- **Items processed** (e.g., "15 of 20 items processed")
- **Status message** (current operation description)
- **Error details** (for failed tasks)
- **Timestamps** (started/completed times)

### 3. Visual Design
- Color-coded by task type:
  - **Data Collection**: Teal (#75c9c8)
  - **Data Analysis**: Purple (#665775)
  - **Report Generation**: Blue (#80a1d4)
- Status-based coloring:
  - **Running**: Task color with spinning icon
  - **Completed**: Green (#58A13B) with checkmark
  - **Failed**: Red (#EA4A4A) with error icon
- Animated progress bars for running tasks
- Expandable/collapsible detail sections
- Dismissible when complete/failed

### 4. User Interactions
- **Click to expand** - View detailed information
- **Dismiss button** - Remove completed/failed tasks
- **Auto-dismiss** - Tasks older than 24 hours automatically filter out
- **Responsive** - Adapts to screen size

### 5. Email Notifications
- **Sends email** when task completes (success or failure)
- **HTML formatted emails** with brand colors
- Includes:
  - Task type and brand name
  - Completion status
  - Error details (if failed)
  - Link back to TALES app
- SMTP configuration via environment variables

## Implementation Details

### Backend Components

#### 1. API Endpoint (`app/routers/tasks.py`)
```python
GET /tasks/status
```
- Returns active and recently completed tasks (last 24 hours)
- Filters by current user and active brand
- Returns running, completed, failed, and cancelled tasks

#### 2. Email Service (`app/services/email_notifications.py`)
```python
send_task_completion_email(db, user_id, task_type, task_id, status, brand_id, error_message)
```
- Sends HTML emails via SMTP
- Separate templates for success/failure
- Configurable via environment variables:
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USER`
  - `SMTP_PASSWORD`
  - `SMTP_FROM_EMAIL`
  - `SMTP_FROM_NAME`
  - `FRONTEND_URL`

### Frontend Components

#### 1. React Context (`frontend/src/contexts/TaskStatusContext.tsx`)
- Manages task state globally
- Polls backend every 5 seconds
- Handles task dismissal
- Filters dismissed tasks

#### 2. Banner Component (`frontend/src/components/TaskStatusBanner.tsx`)
- Fixed position overlay
- Renders task cards
- Animated progress indicators
- Expandable details
- Dismissible tasks

#### 3. Integration (`frontend/src/App.tsx`)
- Wraps entire app in `TaskStatusProvider`
- Renders `TaskStatusBanner` at app root
- Available on all protected routes

## Usage

### For Development
1. **Backend**: Already running on localhost:8000
2. **Frontend**: Already running on localhost:5173
3. **Test**: Create a task status entry in database to see banner appear

### For Production
1. **Configure SMTP** environment variables in `.env`:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM_EMAIL=noreply@yourdomain.com
   SMTP_FROM_NAME=TALES
   FRONTEND_URL=https://tales.robotrachel.com
   ```

2. **Update task completion handlers** to call email service:
   ```python
   from app.services.email_notifications import send_task_completion_email

   # After task completes
   send_task_completion_email(
       db=db,
       user_id=user_id,
       task_type='collection',  # or 'analysis', 'report_generation'
       task_id=task.id,
       status='completed',  # or 'failed'
       brand_id=brand_id,
       error_message=None  # or error string if failed
   )
   ```

3. **Deploy** as usual - no additional dependencies needed (all required packages already in requirements.txt)

## Database Schema

Uses existing `TaskStatus` model:
- `id`: Primary key
- `user_id`: FK to users
- `brand_id`: FK to brand_info (nullable)
- `task_type`: 'collection', 'analysis', 'report_generation'
- `status`: 'running', 'completed', 'failed', 'cancelled'
- `progress`: 0-100
- `total_items`: Total items to process
- `processed_items`: Items processed so far
- `message`: Current status message
- `error_message`: Error details
- `started_at`: Task start time
- `completed_at`: Task completion time
- `updated_at`: Last update time

## Future Enhancements (Optional)

1. **Browser Notifications**: Request permission and send browser notifications when tasks complete
2. **Cancel Tasks**: Add ability to cancel running tasks from banner
3. **Task History**: Dedicated page showing all task history
4. **Progress Details**: Show what specific item is being processed
5. **Estimated Time**: Calculate and display ETA for task completion
6. **Sound Notifications**: Optional sound when task completes
7. **Task Dependencies**: Show if tasks are waiting on other tasks

## Testing Locally

To test the banner without running a full collection:

```python
# In Python shell or script
from app.database import SessionLocal
from app import models
import datetime

db = SessionLocal()

# Create a test task
task = models.TaskStatus(
    user_id=YOUR_USER_ID,
    brand_id=YOUR_BRAND_ID,
    task_type='collection',
    status='running',
    progress=45,
    total_items=20,
    processed_items=9,
    message='Collecting responses from ChatGPT...',
    started_at=datetime.datetime.utcnow()
)
db.add(task)
db.commit()

# Banner will appear automatically!
# To complete it:
task.status = 'completed'
task.progress = 100
task.processed_items = 20
task.completed_at = datetime.datetime.utcnow()
db.commit()
```

## Files Modified/Created

### Backend
- `app/routers/tasks.py` (NEW)
- `app/services/email_notifications.py` (NEW)
- `app/main.py` (MODIFIED - added tasks router)

### Frontend
- `frontend/src/contexts/TaskStatusContext.tsx` (NEW)
- `frontend/src/components/TaskStatusBanner.tsx` (NEW)
- `frontend/src/App.tsx` (MODIFIED - integrated context and banner)

## Notes

- The banner only shows for tasks in the last 24 hours
- Tasks are filtered by the currently active brand
- Email notifications require SMTP configuration
- The banner polls every 5 seconds - adjust interval in `TaskStatusContext.tsx` if needed
- Dismissed tasks are stored in component state (resets on page refresh)
