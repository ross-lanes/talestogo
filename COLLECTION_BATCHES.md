# Collection Batches Feature

## Overview

The Collection Batches feature allows you to track and manage data collections as discrete batches, making it easier to:
- Organize data collections by date/time
- Delete incomplete collections easily
- Run analysis on specific batches
- Compare different time periods
- Track collection metadata (query count, platforms used, etc.)

## Database Schema

### New Table: `collection_batches`

```sql
CREATE TABLE collection_batches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    brand_id INTEGER REFERENCES brand_info(id),
    batch_name VARCHAR(200) NOT NULL,          -- e.g., "Collection 2025-01-15"
    description TEXT,                           -- Optional notes about this collection
    started_at TIMESTAMP NOT NULL,              -- When collection began
    completed_at TIMESTAMP,                     -- When collection finished (NULL if in progress)
    status VARCHAR(20) DEFAULT 'in_progress',  -- in_progress, completed, failed
    total_queries INTEGER DEFAULT 0,            -- Number of queries in this batch
    total_responses INTEGER DEFAULT 0,          -- Number of responses collected
    platforms TEXT,                             -- Comma-separated: "ChatGPT, Claude, Gemini, Perplexity"
    notes TEXT,                                 -- Additional notes
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Updated Table: `responses`

Added `batch_id` column:
```sql
ALTER TABLE responses
ADD COLUMN batch_id INTEGER REFERENCES collection_batches(id);
```

## Migration

Run the migration to add batch tracking to your database:

```bash
# For local database:
DATABASE_URL="postgresql://localhost/tales_db" python3 migrations/add_collection_batches.py

# For production:
DATABASE_URL="postgresql://user:pass@host/db" python3 migrations/add_collection_batches.py
```

The migration will:
1. Create the `collection_batches` table
2. Add `batch_id` column to responses
3. Automatically group existing responses into batches by date

## Usage

### 1. Starting a Collection (Backend)

When starting a new collection, create a batch record:

```python
from app.models import CollectionBatch
import datetime

# Create new batch
batch = CollectionBatch(
    user_id=current_user.id,
    brand_id=brand_id,
    batch_name=f"Collection {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    description="Regular weekly collection",
    started_at=datetime.datetime.utcnow(),
    status='in_progress',
    platforms="ChatGPT, Claude, Gemini, Perplexity"
)
db.add(batch)
db.commit()

# When creating responses, link them to the batch:
response = Response(
    user_id=user_id,
    brand_id=brand_id,
    batch_id=batch.id,  # Link to batch
    query_id=query_id,
    platform=platform,
    # ... other fields
)
```

### 2. Completing a Collection

When collection finishes:

```python
batch = db.query(CollectionBatch).filter_by(id=batch_id).first()
batch.completed_at = datetime.datetime.utcnow()
batch.status = 'completed'
batch.total_queries = db.query(Response).filter_by(batch_id=batch_id).count()
batch.total_responses = batch.total_queries * 4  # 4 platforms
db.commit()
```

### 3. Listing Batches

Get all batches for a user:

```python
batches = db.query(CollectionBatch)\
    .filter_by(user_id=user_id, brand_id=brand_id)\
    .order_by(CollectionBatch.started_at.desc())\
    .all()

for batch in batches:
    print(f"{batch.batch_name}: {batch.total_responses} responses ({batch.status})")
```

### 4. Running Analysis on a Specific Batch

Filter analytics by batch:

```python
# Get responses from a specific batch
responses = db.query(Response)\
    .filter_by(user_id=user_id, brand_id=brand_id, batch_id=batch_id)\
    .all()

# Or use in analytics functions:
def get_dashboard_metrics(db, user_id, brand_id, batch_id=None):
    query = db.query(Response).filter_by(user_id=user_id, brand_id=brand_id)

    if batch_id:
        query = query.filter_by(batch_id=batch_id)

    # ... rest of analytics
```

### 5. Deleting a Batch

Delete a batch and all its responses:

```python
# Delete all responses in the batch
db.query(Response).filter_by(batch_id=batch_id).delete()

# Delete the batch record
db.query(CollectionBatch).filter_by(id=batch_id).delete()

db.commit()
```

## Frontend Integration

### Batch Selector Component

Add a batch selector to analysis pages:

```typescript
interface CollectionBatch {
  id: number;
  batch_name: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  total_responses: number;
  platforms: string;
}

// Fetch batches
const { data: batches } = useQuery({
  queryKey: ['collection-batches'],
  queryFn: async () => {
    const response = await api.get('/batches/');
    return response.data;
  }
});

// Batch selector
<FormControl fullWidth>
  <InputLabel>Collection Batch</InputLabel>
  <Select
    value={selectedBatchId}
    onChange={(e) => setSelectedBatchId(e.target.value)}
  >
    <MenuItem value="">All Data</MenuItem>
    {batches?.map((batch) => (
      <MenuItem key={batch.id} value={batch.id}>
        {batch.batch_name} - {batch.total_responses} responses
      </MenuItem>
    ))}
  </Select>
</FormControl>

// Use in analytics queries
const { data: metrics } = useQuery({
  queryKey: ['dashboard-metrics', selectedBatchId],
  queryFn: async () => {
    const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
    const response = await api.get('/analytics/dashboard', { params });
    return response.data;
  }
});
```

## API Endpoints to Add

### GET /batches/
List all batches for current user:
```json
[
  {
    "id": 1,
    "batch_name": "Collection 2025-01-15 10:30",
    "started_at": "2025-01-15T10:30:00",
    "completed_at": "2025-01-15T11:45:00",
    "status": "completed",
    "total_queries": 50,
    "total_responses": 200,
    "platforms": "ChatGPT, Claude, Gemini, Perplexity"
  }
]
```

### GET /batches/{batch_id}
Get batch details

### POST /batches/
Create new batch (called when starting collection)

### DELETE /batches/{batch_id}
Delete batch and all associated responses

### GET /analytics/dashboard?batch_id={id}
Get dashboard metrics filtered by batch

## Benefits

1. **Easy Cleanup**: Delete incomplete collections by batch ID instead of by date
2. **Historical Analysis**: Compare metrics across different time periods
3. **Metadata Tracking**: Track which platforms were used, how many queries, etc.
4. **Better Organization**: Give meaningful names to collections
5. **Progress Tracking**: See status of ongoing collections

## Implementation Checklist

- [x] Create migration script
- [x] Add CollectionBatch model
- [x] Update Response model with batch_id
- [ ] Update collection API to create batches
- [ ] Add batch endpoints (list, get, delete)
- [ ] Update analytics functions to accept batch_id parameter
- [ ] Add batch selector to frontend
- [ ] Update delete script to work with batch IDs
- [ ] Add batch management UI page

## Example: Updating Collection API

```python
@router.post("/tasks/run-collection/")
async def run_collection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create batch record
    batch = CollectionBatch(
        user_id=current_user.id,
        brand_id=current_user.active_brand_id,
        batch_name=f"Collection {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        started_at=datetime.datetime.utcnow(),
        status='in_progress',
        platforms="ChatGPT, Claude, Gemini, Perplexity"
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Run collection (pass batch.id to collector)
    # When creating responses, set batch_id=batch.id

    # After collection completes:
    batch.completed_at = datetime.datetime.utcnow()
    batch.status = 'completed'
    batch.total_responses = db.query(Response).filter_by(batch_id=batch.id).count()
    db.commit()

    return {"message": "Collection completed", "batch_id": batch.id}
```
