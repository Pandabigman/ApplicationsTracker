# Job Tracker API - Backend

FastAPI backend for the Job Tracker application with SQLite database and GPT-4 powered job scraping.

## Features

- **SQLite Database**: Lightweight, file-based database (no server required)
- **GPT-4 Job Scraping**: Intelligent extraction of job details from any job posting URL
- **Multi-table Schema**: Organized data structure with relationships
- **Activity Tracking**: Automatic logging of status changes and user actions
- **Timestamped Notes**: Add and manage multiple notes per application
- **Excel Export**: Export all applications to a spreadsheet
- **RESTful API**: Full CRUD operations with FastAPI

## Database Schema

### Tables

1. **applications** - Main application tracking
   - Core job information (company, position, location, salary)
   - Status tracking (Applied, Interview, Offer, Rejected, etc.)
   - Dates (applied, deadline)

2. **job_details** - Detailed job information
   - Full job description
   - Requirements/qualifications
   - Clean text content from scraping

3. **notes** - Timestamped notes
   - Multiple notes per application
   - Edit history with timestamps

4. **activity_log** - Activity tracking
   - Status changes
   - Note additions/updates
   - Application creation

## Setup

### 1. Install Dependencies

```bash
cd logic
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `logic` directory:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_actual_api_key_here
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Run Migration (Optional)

If you have existing PostgreSQL data to migrate:

```bash
python migrate_to_sqlite.py
```

This will:
- Create the SQLite database
- Transfer all data from PostgreSQL
- Convert old notes to the new format

### 4. Start the Server

```bash
cd app
python main.py
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at: http://localhost:8000

## API Documentation

Once the server is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Applications

- `GET /applications` - Get all applications
- `GET /applications/{id}` - Get single application with notes and activities
- `POST /applications` - Create new application
- `PUT /applications/{id}` - Update application
- `DELETE /applications/{id}` - Delete application

### Job Details

- `POST /applications/{id}/job-details` - Add job details
- `PUT /applications/{id}/job-details` - Update job details

### Notes

- `GET /applications/{id}/notes` - Get all notes for an application
- `POST /applications/{id}/notes` - Add a new note
- `PUT /notes/{note_id}` - Update a note
- `DELETE /notes/{note_id}` - Delete a note

### Activities

- `GET /applications/{id}/activities` - Get activity log

### Scraping

- `POST /scrape` - Scrape job details from URL
  ```json
  {
    "url": "https://example.com/job-posting"
  }
  ```

### Export

- `GET /export/excel` - Download all applications as Excel file

## GPT-4 Scraping

The scraper:
1. Fetches HTML from the job posting URL
2. Extracts clean text (removes nav, ads, etc.)
3. Sends to GPT-4 for structured extraction
4. Returns: company, position, location, salary, description, requirements

**Note**: Each scrape uses GPT-4 API tokens (costs apply).

## Database Location

The SQLite database is stored at:
```
logic/data/jobtracker.db
```

This file contains all your data. Back it up regularly!

## Migration from PostgreSQL

The old PostgreSQL schema had a single table with all fields. The new schema:
- Separates job details into their own table
- Supports multiple timestamped notes instead of one note field
- Adds activity tracking
- Uses SQLite instead of PostgreSQL

The migration script automatically handles this conversion.

## Development

### Project Structure

```
logic/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app & endpoints
│   ├── database.py       # Database connection
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   └── scrape.py         # GPT-4 scraping logic
├── data/
│   └── jobtracker.db     # SQLite database
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── .env.example          # Example environment file
└── migrate_to_sqlite.py  # Migration script

```

### Adding New Features

1. **New Database Fields**: Update `models.py` and `schemas.py`
2. **New Endpoints**: Add to `main.py`
3. **New Scraping Logic**: Modify `scrape.py`

## Troubleshooting

### "OPENAI_API_KEY not configured"
- Make sure you created `.env` file in the `logic` directory
- Verify your API key is correct

### "Module not found" errors
- Run `pip install -r requirements.txt` in the logic directory

### Database errors
- Delete `logic/data/jobtracker.db` to start fresh
- Or run the migration script again

## Security Notes

- Never commit `.env` file to version control
- Keep your OpenAI API key secret
- The SQLite database file contains all your data - protect it

## Cost Considerations

GPT-4 API usage has costs:
- Current pricing: ~$0.01-0.03 per job scrape
- Consider using GPT-3.5-turbo for lower costs (change model in `scrape.py`)
- Or implement caching for repeated scrapes

## Future Enhancements

Potential improvements:
- Add authentication/user management
- Implement job search tracking (searches you've done)
- Add reminders for follow-ups
- Integration with job boards APIs
- Email notifications for deadlines
