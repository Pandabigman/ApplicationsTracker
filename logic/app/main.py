import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Depends, HTTPException, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from typing import List
import io
from openpyxl import Workbook

from app.database import get_db
from app.models import Application, JobDetail, Note, ActivityLog, Deadline
from app.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    JobDetailCreate,
    JobDetailUpdate,
    JobDetailResponse,
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    ActivityLogResponse,
    DeadlineCreate,
    DeadlineUpdate,
    DeadlineResponse,
    ScrapeRequest,
    ScrapeResponse,
)
from app.scrape import JobScraper
from app.auth import get_current_user

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Application Tracker API", version="3.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - configurable via environment
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
allowed_origins = [frontend_url]
if "http://localhost:5173" not in allowed_origins:
    allowed_origins.append("http://localhost:5173")
if "http://localhost:3000" not in allowed_origins:
    allowed_origins.append("http://localhost:3000")
if "http://127.0.0.1:5173" not in allowed_origins:
    allowed_origins.append("http://127.0.0.1:5173")
if "http://127.0.0.1:3000" not in allowed_origins:
    allowed_origins.append("http://127.0.0.1:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Gemini-Api-Key"],
)

scraper = JobScraper()


def _get_user_application(
    application_id: int, user_id: str, db: Session
) -> Application:
    """Helper to fetch an application ensuring it belongs to the current user."""
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


# ============== Health Check ==============


@app.get("/")
def read_root():
    return {
        "message": "Application Tracker API v3.0",
        "status": "running",
        "database": "PostgreSQL",
    }


# ============== Scraping Endpoints ==============


@app.post("/scrape", response_model=ScrapeResponse)
@limiter.limit("20/minute")
async def scrape_job(
    request: Request,
    body: ScrapeRequest,
    x_gemini_api_key: str = Header(...),
    _user_id: str = Depends(get_current_user),
):
    """Scrape job details from a URL using Gemini AI (BYOK)"""
    try:
        data = await scraper.scrape_url(str(body.url), x_gemini_api_key)

        if not data.get("position_title") and not data.get("company_name"):
            raise HTTPException(
                status_code=400,
                detail="Could not extract job information from this URL. Please enter details manually.",
            )

        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Scrape error: {e}")
        raise HTTPException(status_code=400, detail="Failed to extract job info from this URL.")


@app.post("/validate-key")
@limiter.limit("10/minute")
async def validate_key(
    request: Request,
    x_gemini_api_key: str = Header(...),
    _user_id: str = Depends(get_current_user),
):
    """Validate a Gemini API key with a minimal test call"""
    try:
        import google.generativeai as genai

        genai.configure(api_key=x_gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        await model.generate_content_async("Say 'ok'")
        return {"valid": True}
    except Exception as e:
        print(f"Key validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid API key.")


# ============== Application Endpoints ==============


@app.get("/applications", response_model=List[ApplicationResponse])
def get_applications(
    db: Session = Depends(get_db), user_id: str = Depends(get_current_user)
):
    """Get all applications for the current user"""
    applications = (
        db.query(Application)
        .filter(Application.user_id == user_id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return applications


@app.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get a single application with all related data"""
    return _get_user_application(application_id, user_id, db)


@app.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a new application"""
    db_application = Application(
        user_id=user_id,
        company_name=application.company_name,
        position_title=application.position_title,
        job_url=application.job_url,
        location=application.location,
        salary=application.salary,
        status=application.status or "Applied",
        deadline=application.deadline,
        date_applied=application.date_applied,
    )
    db.add(db_application)
    db.commit()
    db.refresh(db_application)

    activity = ActivityLog(
        application_id=db_application.id,
        activity_type="application_created",
        description=f"Applied to {application.position_title} at {application.company_name}",
        new_value=db_application.status,
    )
    db.add(activity)
    db.commit()

    return db_application


@app.put("/applications/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    application: ApplicationUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Update an existing application"""
    db_application = _get_user_application(application_id, user_id, db)
    old_status = db_application.status

    update_data = application.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_application, key, value)

    db.commit()
    db.refresh(db_application)

    if application.status and application.status != old_status:
        activity = ActivityLog(
            application_id=db_application.id,
            activity_type="status_change",
            description=f"Status changed from {old_status} to {application.status}",
            old_value=old_status,
            new_value=application.status,
        )
        db.add(activity)
        db.commit()

    return db_application


@app.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Delete an application (cascades to all related data)"""
    db_application = _get_user_application(application_id, user_id, db)
    db.delete(db_application)
    db.commit()
    return None


# ============== Job Details Endpoints ==============


@app.post(
    "/applications/{application_id}/job-details",
    response_model=JobDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job_details(
    application_id: int,
    job_detail: JobDetailCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create job details for an application"""
    _get_user_application(application_id, user_id, db)

    existing = (
        db.query(JobDetail).filter(JobDetail.application_id == application_id).first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Job details already exist for this application"
        )

    db_job_detail = JobDetail(
        application_id=application_id,
        description=job_detail.description,
        requirements=job_detail.requirements,
        clean_text_content=job_detail.clean_text_content,
        ai_thoughts=job_detail.ai_thoughts,
    )
    db.add(db_job_detail)
    db.commit()
    db.refresh(db_job_detail)
    return db_job_detail


@app.put("/applications/{application_id}/job-details", response_model=JobDetailResponse)
def update_job_details(
    application_id: int,
    job_detail: JobDetailUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Update job details for an application"""
    _get_user_application(application_id, user_id, db)

    db_job_detail = (
        db.query(JobDetail).filter(JobDetail.application_id == application_id).first()
    )
    if not db_job_detail:
        raise HTTPException(status_code=404, detail="Job details not found")

    update_data = job_detail.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_job_detail, key, value)

    db.commit()
    db.refresh(db_job_detail)
    return db_job_detail


# ============== Notes Endpoints ==============


@app.get("/applications/{application_id}/notes", response_model=List[NoteResponse])
def get_notes(
    application_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get all notes for an application"""
    _get_user_application(application_id, user_id, db)
    notes = (
        db.query(Note)
        .filter(Note.application_id == application_id)
        .order_by(Note.created_at.desc())
        .all()
    )
    return notes


@app.post(
    "/applications/{application_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    application_id: int,
    note: NoteCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a new note for an application"""
    _get_user_application(application_id, user_id, db)

    db_note = Note(application_id=application_id, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    activity = ActivityLog(
        application_id=application_id,
        activity_type="note_added",
        description="Added a new note",
    )
    db.add(activity)
    db.commit()

    return db_note


@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note: NoteUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Update an existing note"""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    _get_user_application(db_note.application_id, user_id, db)

    db_note.content = note.content
    db.commit()
    db.refresh(db_note)

    activity = ActivityLog(
        application_id=db_note.application_id,
        activity_type="note_updated",
        description="Updated a note",
    )
    db.add(activity)
    db.commit()

    return db_note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Delete a note"""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    _get_user_application(db_note.application_id, user_id, db)

    application_id = db_note.application_id
    db.delete(db_note)
    db.commit()

    activity = ActivityLog(
        application_id=application_id,
        activity_type="note_deleted",
        description="Deleted a note",
    )
    db.add(activity)
    db.commit()

    return None


# ============== Activity Log Endpoints ==============


@app.get(
    "/applications/{application_id}/activities",
    response_model=List[ActivityLogResponse],
)
def get_activities(
    application_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get activity log for an application"""
    _get_user_application(application_id, user_id, db)
    activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.application_id == application_id)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )
    return activities


# ============== Deadline Endpoints ==============


@app.get(
    "/applications/{application_id}/deadlines", response_model=List[DeadlineResponse]
)
def get_deadlines(
    application_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get all deadlines for an application"""
    _get_user_application(application_id, user_id, db)
    deadlines = (
        db.query(Deadline)
        .filter(Deadline.application_id == application_id)
        .order_by(Deadline.deadline_date.asc())
        .all()
    )
    return deadlines


@app.post(
    "/applications/{application_id}/deadlines",
    response_model=DeadlineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deadline(
    application_id: int,
    deadline: DeadlineCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a new deadline for an application"""
    _get_user_application(application_id, user_id, db)

    db_deadline = Deadline(
        application_id=application_id,
        deadline_type=deadline.deadline_type,
        deadline_date=deadline.deadline_date,
        description=deadline.description,
        is_completed=deadline.is_completed or False,
    )
    db.add(db_deadline)
    db.commit()
    db.refresh(db_deadline)

    activity = ActivityLog(
        application_id=application_id,
        activity_type="deadline_added",
        description=f'Added {deadline.deadline_type} deadline for {deadline.deadline_date.strftime("%Y-%m-%d")}',
    )
    db.add(activity)
    db.commit()

    return db_deadline


@app.put("/deadlines/{deadline_id}", response_model=DeadlineResponse)
def update_deadline(
    deadline_id: int,
    deadline: DeadlineUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Update an existing deadline"""
    db_deadline = db.query(Deadline).filter(Deadline.id == deadline_id).first()
    if not db_deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
    _get_user_application(db_deadline.application_id, user_id, db)

    old_completed = bool(db_deadline.is_completed)

    update_data = deadline.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_deadline, key, value)

    db.commit()
    db.refresh(db_deadline)

    new_completed = bool(db_deadline.is_completed)
    if new_completed != old_completed:
        activity = ActivityLog(
            application_id=db_deadline.application_id,
            activity_type=(
                "deadline_completed" if new_completed else "deadline_reopened"
            ),
            description=f'{db_deadline.deadline_type} deadline {"completed" if new_completed else "reopened"}',
        )
        db.add(activity)
        db.commit()

    return db_deadline


@app.delete("/deadlines/{deadline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Delete a deadline"""
    db_deadline = db.query(Deadline).filter(Deadline.id == deadline_id).first()
    if not db_deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
    _get_user_application(db_deadline.application_id, user_id, db)

    application_id = db_deadline.application_id
    db.delete(db_deadline)
    db.commit()

    activity = ActivityLog(
        application_id=application_id,
        activity_type="deadline_deleted",
        description="Deleted a deadline",
    )
    db.add(activity)
    db.commit()

    return None


# ============== Export Endpoints ==============


@app.get("/export/excel")
def export_to_excel(
    db: Session = Depends(get_db), user_id: str = Depends(get_current_user)
):
    """Export all applications to Excel"""
    applications = (
        db.query(Application)
        .filter(Application.user_id == user_id)
        .order_by(Application.created_at.desc())
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Applications"

    headers = [
        "ID",
        "Company",
        "Position",
        "Location",
        "Salary",
        "Status",
        "Date Applied",
        "Deadline",
        "Job URL",
        "Latest Note",
    ]
    ws.append(headers)

    for app_item in applications:
        latest_note = ""
        if app_item.notes:
            latest_note = app_item.notes[0].content if len(app_item.notes) > 0 else ""

        ws.append(
            [
                app_item.id,
                app_item.company_name,
                app_item.position_title,
                app_item.location or "",
                app_item.salary or "",
                app_item.status,
                app_item.date_applied.strftime("%Y-%m-%d") if app_item.date_applied else "",
                app_item.deadline.strftime("%Y-%m-%d") if app_item.deadline else "",
                app_item.job_url or "",
                latest_note,
            ]
        )

    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=applications.xlsx"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
