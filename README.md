# Job Tracker

A full-stack application to track job applications, scrape job postings, and manage your job search workflow.

## Features

- **Job URL Scraping** - Paste a job posting URL and automatically extract company name, position, location, salary, and requirements using AI
- **Application Management** - Track application status (Applied, Interview, Offer, Rejected, etc.)
- **Notes & Deadlines** - Add notes and set deadlines for each application
- **Activity Log** - Automatic tracking of all changes and updates
- **Excel Export** - Export all applications to Excel spreadsheet

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 19, Vite, Bootstrap 5 |
| Backend | FastAPI, Python 3.11+, SQLAlchemy |
| Database | SQLite |
| Scraping | Playwright, OpenAI GPT-4 |

## Prerequisites

### For Local Development
- Python 3.11+
- Node.js 20+
- OpenAI API key (for job scraping feature)

### For Docker
- Docker & Docker Compose
- OpenAI API key (for job scraping feature)

## Quick Start

### Option 1: Using Quick Start Scripts

**Linux/macOS:**
```bash
./quickstart.sh
```

**Windows:**
```bash
quickstart.bat
```

**macOS (double-click):**
Double-click `quickstart.command` in Finder.

### Option 2: Using Docker (Recommended)

1. Clone the repository and navigate to the project folder

2. Create environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

4. Start the application:
   ```bash
   docker-compose up
   ```

5. Access the app at http://localhost:5173

To run in background:
```bash
docker-compose up -d
```

To stop:
```bash
docker-compose down
```

### Option 3: Manual Setup

#### Backend Setup

```bash
cd logic

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Set environment variable
export OPENAI_API_KEY=your_api_key_here    # Linux/macOS
set OPENAI_API_KEY=your_api_key_here       # Windows

# Start server
python -m uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
cd view

# Install dependencies
npm install

# Start development server
npm run dev
```

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |

## Usage Guide

### Adding a Job Application

1. Click **"Add Application"** button
2. Either:
   - **Paste a job URL** and click "Scrape" to auto-fill details
   - **Manually enter** company name, position, and other details
3. Click **"Save"** to create the application

### Managing Applications

- **Change Status** - Click on an application and update the status dropdown
- **Add Notes** - Use the notes section to track conversations, interview feedback, etc.
- **Set Deadlines** - Add important dates like interview schedules or follow-up reminders
- **View Activity** - Check the activity log to see all changes made to an application

### Exporting Data

Click the **"Export to Excel"** button to download all applications as an Excel file.

## Project Structure

```
ApplicationsTracker/
├── logic/                  # Backend (FastAPI)
│   ├── app/
│   │   ├── main.py        # API endpoints
│   │   ├── models.py      # Database models
│   │   ├── schemas.py     # Pydantic schemas
│   │   ├── database.py    # Database configuration
│   │   └── scrape.py      # Job scraping logic
│   ├── data/              # SQLite database (auto-created)
│   ├── requirements.txt
│   └── Dockerfile
├── view/                   # Frontend (React)
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API client
│   │   └── App.jsx        # Main app component
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── quickstart.sh          # Linux/macOS launcher
├── quickstart.bat         # Windows launcher
└── quickstart.command     # macOS double-click launcher
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/applications` | List all applications |
| POST | `/applications` | Create new application |
| GET | `/applications/{id}` | Get application details |
| PUT | `/applications/{id}` | Update application |
| DELETE | `/applications/{id}` | Delete application |
| POST | `/scrape` | Scrape job details from URL |
| GET | `/export/excel` | Export to Excel |

Full API documentation available at http://localhost:8000/docs when the server is running.

## Troubleshooting

### Scraping not working
- Ensure `OPENAI_API_KEY` is set correctly
- Some job sites may block automated scraping

### Port already in use
- Backend: Change port with `--port 8001` flag
- Frontend: Vite will automatically use next available port

### Database errors
- Delete `logic/data/jobtracker.db` to reset the database

## License

MIT
