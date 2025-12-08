# Migration Guide: PostgreSQL to SQLite with GPT-4 Scraping

## Summary of Changes

This migration updates the Job Tracker backend from PostgreSQL to SQLite with a multi-table schema and GPT-4-powered job scraping.

## What Changed

### 1. Database Migration
- **Before**: PostgreSQL with single `applications` table
- **After**: SQLite with 4 tables (`applications`, `job_details`, `notes`, `activity_log`)

### 2. Schema Changes

#### Applications Table
- Removed: `description`, `requirements`, `notes` fields
- These moved to separate tables for better organization

#### New Tables
- **job_details**: Stores job description, requirements, and scraped content
- **notes**: Supports multiple timestamped notes per application
- **activity_log**: Tracks all changes (status updates, note additions, etc.)

### 3. Scraping Engine
- **Before**: Site-specific scrapers (LinkedIn, Indeed, etc.)
- **After**: Universal GPT-4-based scraper that works with any job posting URL

### 4. Dependencies
- **Removed**: `psycopg2-binary` (PostgreSQL driver)
- **Added**: `openai` (GPT-4 API)
- **Kept**: SQLAlchemy (works with both databases)

## Files Modified

### Backend Files
1. **[database.py](logic/app/database.py)** - SQLite configuration
2. **[models.py](logic/app/models.py)** - New multi-table schema
3. **[schemas.py](logic/app/schemas.py)** - Updated Pydantic schemas
4. **[scrape.py](logic/app/scrape.py)** - GPT-4 scraping implementation
5. **[main.py](logic/app/main.py)** - New API endpoints for notes and activities
6. **[requirements.txt](logic/requirements.txt)** - Updated dependencies

### New Files
1. **[migrate_to_sqlite.py](logic/migrate_to_sqlite.py)** - Migration script
2. **[setup.py](logic/setup.py)** - Interactive setup helper
3. **[.env.example](logic/.env.example)** - Environment variable template
4. **[README.md](logic/README.md)** - Complete documentation

## Migration Steps

### Option 1: Fresh Start (Recommended for New Users)

```bash
cd logic

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py

# Start the server
cd app
python main.py
```

### Option 2: Migrate Existing PostgreSQL Data

```bash
cd logic

# Install new dependencies
pip install -r requirements.txt

# Make sure your .env has PostgreSQL DATABASE_URL
# Run migration
python migrate_to_sqlite.py

# Start the server
cd app
python main.py
```

## API Changes

### New Endpoints

#### Notes Management
- `GET /applications/{id}/notes` - Get all notes
- `POST /applications/{id}/notes` - Create note
- `PUT /notes/{note_id}` - Update note
- `DELETE /notes/{note_id}` - Delete note

#### Job Details
- `POST /applications/{id}/job-details` - Add job details
- `PUT /applications/{id}/job-details` - Update job details

#### Activity Log
- `GET /applications/{id}/activities` - View activity history

### Modified Endpoints

#### GET /applications and GET /applications/{id}
Now returns nested data:
```json
{
  "id": 1,
  "company_name": "Google",
  "position_title": "Software Engineer",
  "status": "Applied",
  "notes": [
    {
      "id": 1,
      "content": "First note",
      "created_at": "2025-01-01T10:00:00"
    }
  ],
  "activities": [
    {
      "id": 1,
      "activity_type": "status_change",
      "description": "Status changed from Applied to Interview",
      "created_at": "2025-01-02T15:00:00"
    }
  ],
  "job_details": {
    "description": "...",
    "requirements": "..."
  }
}
```

## Frontend Updates Needed

### 1. Notes UI
- Change from single text field to list of notes
- Add "Add Note" button
- Show timestamps for each note
- Allow editing/deleting individual notes

### 2. Activity Timeline
- Display activity log in timeline format
- Show status changes, note additions, etc.

### 3. API Calls
Update API calls to use new endpoints:

**Before:**
```javascript
// Single notes field
PUT /applications/{id}
{
  "notes": "My note"
}
```

**After:**
```javascript
// Multiple notes
POST /applications/{id}/notes
{
  "content": "My new note"
}

GET /applications/{id}/notes
// Returns array of notes
```

## Configuration

### Environment Variables

Create `logic/.env`:

```env
# Required for GPT-4 scraping
OPENAI_API_KEY=sk-...

# Optional: Specify database (defaults to SQLite)
# DATABASE_URL=sqlite:///data/jobtracker.db
```

### API Key Setup

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add to `.env` file
4. Restart the server

## Cost Considerations

### GPT-4 API Costs
- Each job scrape costs approximately $0.01-0.03
- Based on job posting size
- Alternative: Use GPT-3.5-turbo (cheaper, less accurate)

### Switching to GPT-3.5
Edit `logic/app/scrape.py` line 144:
```python
"model": "gpt-3.5-turbo",  # Instead of "gpt-4"
```

## Database Location

- **SQLite Database**: `logic/data/jobtracker.db`
- **Backup**: Just copy this file
- **Reset**: Delete this file to start fresh

## Rollback Plan

If you need to rollback to PostgreSQL:

1. Keep your old PostgreSQL database
2. The old code is in git history
3. Revert these files to previous versions:
   - `database.py`
   - `models.py`
   - `schemas.py`
   - `scrape.py`
   - `requirements.txt`

## Testing the Migration

### 1. Test Database Connection
```bash
cd logic/app
python -c "from database import engine; print(engine.url)"
# Should show: sqlite:///...
```

### 2. Test API
```bash
# Start server
python main.py

# In another terminal
curl http://localhost:8000/
# Should return: {"message": "Application Tracker API v2.0", "database": "SQLite"}
```

### 3. Test Scraping
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/job"}'
```

## Troubleshooting

### "OPENAI_API_KEY not configured"
- Create `.env` file in `logic` directory
- Add your API key

### "No module named 'openai'"
- Run `pip install -r requirements.txt`

### "Database is locked"
- SQLite doesn't support concurrent writes well
- For production, consider PostgreSQL or add connection pooling

### Old PostgreSQL data not appearing
- Check `.env` has correct DATABASE_URL
- Run migration script: `python migrate_to_sqlite.py`

## Questions?

Check the [README.md](logic/README.md) for detailed documentation.

## Benefits of New System

✅ **No database server needed** - SQLite is file-based
✅ **Universal scraping** - Works with any job site
✅ **Better organization** - Multi-table schema
✅ **Activity tracking** - See all changes
✅ **Multiple notes** - Add notes over time
✅ **Easier backup** - Just one database file
✅ **Lower maintenance** - Less infrastructure
