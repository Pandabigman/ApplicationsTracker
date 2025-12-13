from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
from openpyxl import Workbook

from app.database import engine, get_db, Base
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

# On Windows, the default asyncio event loop policy (ProactorEventLoop) doesn't
# support subprocesses, which Playwright's async API needs to launch browsers.
# This sets a compatible policy (SelectorEventLoop) that does support subprocesses.
# This must be at the top level to run before the event loop is started by uvicorn.
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Application Tracker API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = JobScraper()

# ============== Health Check ==============


@app.get("/")
def read_root():
    return {
        "message": "Application Tracker API v2.0",
        "status": "running",
        "database": "SQLite",
    }


# ============== Scraping Endpoints ==============


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_job(request: ScrapeRequest):
    """Scrape job details from a URL using GPT-4"""
    try:
        data = await scraper.scrape_url(request.url)

        if not data.get("position_title") and not data.get("company_name"):
            raise HTTPException(
                status_code=400,
                detail="Could not extract job information from this URL. Please enter details manually.",
            )

        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Application Endpoints ==============


@app.get("/applications", response_model=List[ApplicationResponse])
def get_applications(db: Session = Depends(get_db)):
    """Get all applications with related data"""
    applications = db.query(Application).order_by(Application.created_at.desc()).all()
    return applications


@app.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: int, db: Session = Depends(get_db)):
    """Get a single application with all related data"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@app.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(application: ApplicationCreate, db: Session = Depends(get_db)):
    """Create a new application"""
    # Create the application
    db_application = Application(
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

    # Create activity log for application creation
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
    application_id: int, application: ApplicationUpdate, db: Session = Depends(get_db)
):
    """Update an existing application"""
    db_application = (
        db.query(Application).filter(Application.id == application_id).first()
    )
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Track status change
    old_status = db_application.status

    # Update fields
    update_data = application.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_application, key, value)

    db.commit()
    db.refresh(db_application)

    # Log status change if status was updated
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
def delete_application(application_id: int, db: Session = Depends(get_db)):
    """Delete an application (cascades to all related data)"""
    db_application = (
        db.query(Application).filter(Application.id == application_id).first()
    )
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

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
    application_id: int, job_detail: JobDetailCreate, db: Session = Depends(get_db)
):
    """Create job details for an application"""
    # Check if application exists
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check if job details already exist
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
    application_id: int, job_detail: JobDetailUpdate, db: Session = Depends(get_db)
):
    """Update job details for an application"""
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
def get_notes(application_id: int, db: Session = Depends(get_db)):
    """Get all notes for an application"""
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
def create_note(application_id: int, note: NoteCreate, db: Session = Depends(get_db)):
    """Create a new note for an application"""
    # Check if application exists
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db_note = Note(application_id=application_id, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    # Log note creation
    activity = ActivityLog(
        application_id=application_id,
        activity_type="note_added",
        description="Added a new note",
    )
    db.add(activity)
    db.commit()

    return db_note


@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note: NoteUpdate, db: Session = Depends(get_db)):
    """Update an existing note"""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")

    db_note.content = note.content
    db.commit()
    db.refresh(db_note)

    # Log note update
    activity = ActivityLog(
        application_id=db_note.application_id,
        activity_type="note_updated",
        description="Updated a note",
    )
    db.add(activity)
    db.commit()

    return db_note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note"""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")

    application_id = db_note.application_id
    db.delete(db_note)
    db.commit()

    # Log note deletion
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
def get_activities(application_id: int, db: Session = Depends(get_db)):
    """Get activity log for an application"""
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
def get_deadlines(application_id: int, db: Session = Depends(get_db)):
    """Get all deadlines for an application"""
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
    application_id: int, deadline: DeadlineCreate, db: Session = Depends(get_db)
):
    """Create a new deadline for an application"""
    # Check if application exists
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db_deadline = Deadline(
        application_id=application_id,
        deadline_type=deadline.deadline_type,
        deadline_date=deadline.deadline_date,
        description=deadline.description,
        is_completed=1 if deadline.is_completed else 0,
    )
    db.add(db_deadline)
    db.commit()
    db.refresh(db_deadline)

    # Log deadline creation
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
    deadline_id: int, deadline: DeadlineUpdate, db: Session = Depends(get_db)
):
    """Update an existing deadline"""
    db_deadline = db.query(Deadline).filter(Deadline.id == deadline_id).first()
    if not db_deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")

    # Track completion status change
    old_completed = bool(db_deadline.is_completed)

    # Update fields
    update_data = deadline.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "is_completed":
            setattr(db_deadline, key, 1 if value else 0)
        else:
            setattr(db_deadline, key, value)

    db.commit()
    db.refresh(db_deadline)

    # Log deadline completion if status changed
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
def delete_deadline(deadline_id: int, db: Session = Depends(get_db)):
    """Delete a deadline"""
    db_deadline = db.query(Deadline).filter(Deadline.id == deadline_id).first()
    if not db_deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")

    application_id = db_deadline.application_id
    db.delete(db_deadline)
    db.commit()

    # Log deadline deletion
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
def export_to_excel(db: Session = Depends(get_db)):
    """Export all applications to Excel"""
    applications = db.query(Application).order_by(Application.created_at.desc()).all()

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Applications"

    # Headers
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

    # Data rows
    for app in applications:
        # Get the latest note if any
        latest_note = ""
        if app.notes:
            latest_note = app.notes[0].content if len(app.notes) > 0 else ""

        ws.append(
            [
                app.id,
                app.company_name,
                app.position_title,
                app.location or "",
                app.salary or "",
                app.status,
                app.date_applied.strftime("%Y-%m-%d") if app.date_applied else "",
                app.deadline.strftime("%Y-%m-%d") if app.deadline else "",
                app.job_url or "",
                latest_note,
            ]
        )

    # Save to BytesIO
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
