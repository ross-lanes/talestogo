# NSTXView Setup Guide

This guide covers the setup steps required to run NSTXView.

## Prerequisites

- Python 3.10+
- Docker (for ChromaDB)
- Google Cloud account with service account credentials

## 1. Database Migration

The NSTXView tables should already be created by running:

```bash
DATABASE_URL="postgresql://..." python migrations/add_nstxview_tables.py
```

## 2. Python Dependencies

Install required packages:

```bash
pip install pymupdf chromadb google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## 3. ChromaDB Setup

### Option A: Local Development (Docker)

Start ChromaDB using Docker Compose:

```bash
docker-compose -f docker-compose.nstxview.yml up -d
```

This starts ChromaDB on `localhost:8000`.

### Option B: ChromaDB Cloud

1. Sign up at https://www.trychroma.com/
2. Create a collection
3. Set environment variables:
   ```bash
   CHROMADB_HOST=your-cloud-host
   CHROMADB_PORT=443
   CHROMA_API_KEY=your-api-key
   ```

### Option C: Self-hosted on Railway

1. Deploy ChromaDB Docker image to Railway
2. Configure environment variables to point to Railway host

## 4. Google Drive API Setup

NSTXView uses a Google Service Account to access the papers folder.

### Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable the **Google Drive API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click Enable
4. Create a Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Name it (e.g., "nstxview-drive-reader")
   - Grant no roles (we just need Drive access)
   - Click "Done"
5. Create a key for the service account:
   - Click on the service account you created
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select JSON format
   - Download and save as `google-service-account.json`

### Share Drive Folder with Service Account

1. Copy the service account email (looks like `name@project.iam.gserviceaccount.com`)
2. Go to your Google Drive folder containing the papers
3. Right-click > Share
4. Add the service account email with "Viewer" access

### Configure Environment

Set the credentials path:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/google-service-account.json"
```

Or for production, store the JSON content in an environment variable and update the code to parse it.

## 5. Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/database

# ChromaDB
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Google Drive
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google-service-account.json
NSTXVIEW_DRIVE_FOLDER_ID=1x3NPuYU_sIbOUyYxzLNcSJByfwZ0AesB

# Anthropic (for LLM extraction)
ANTHROPIC_API_KEY=your-api-key
```

## 6. Logo File

Add the NSTXView logo to the frontend:

```bash
# Place nstxview_white.png in:
frontend/public/nstxview_white.png
```

The logo should be a white icon on transparent background, similar to other product logos in the suite.

## 7. User Access

NSTXView uses user-level access control. To grant access:

1. Log in as an admin
2. Go to Settings > User Management
3. Find the user
4. Add "nstxview" to their allowed products

## 8. Verify Setup

Test the setup by running:

```python
from app.services.nstxview import get_drive_client, get_pdf_processor, get_vector_store

# Test Drive connection
client = get_drive_client()
pdfs = client.list_pdfs()
print(f"Found {len(pdfs)} PDFs in Drive")

# Test PDF processor
processor = get_pdf_processor()
print("PDF processor initialized")

# Test ChromaDB connection
store = get_vector_store()
print(f"ChromaDB connected: {store.is_available()}")
```

## Troubleshooting

### "Google credentials not configured"
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set
- Verify the JSON file exists and is valid

### "Connection refused" for ChromaDB
- Ensure ChromaDB is running: `docker ps`
- Check the port matches `CHROMADB_PORT`

### "Permission denied" on Drive folder
- Verify the service account email is shared with the folder
- Check the folder ID is correct

### User can't see NSTXView
- Verify "nstxview" is in their `allowed_products` array
- Check user is logged in with the correct account
