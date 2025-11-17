from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
from openpyxl import Workbook

from database import engine, get_db, Base
from models import Application
from schemas import (
    ApplicationCreate, 
    ApplicationUpdate, 
    ApplicationResponse,
    ScrapeRequest,
    ScrapeResponse
)
from scrape import JobScraper

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Application Tracker API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = JobScraper()

# Health check
@app.get("/")
def read_root():
    return {"message": "Application Tracker API", "status": "running"}

# Scrape endpoint
@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_job(request: ScrapeRequest):
    try:
        data = scraper.scrape_url(request.url)
        
        if not data.get('position_title') and not data.get('company_name'):
            raise HTTPException(
                status_code=400,
                detail="Could not extract job information from this URL. Please enter details manually."
            )
        
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get all applications
@app.get("/applications", response_model=List[ApplicationResponse])
def get_applications(db: Session = Depends(get_db)):
    applications = db.query(Application).order_by(Application.created_at.desc()).all()
    return applications

# Get single application
@app.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

# Create application
@app.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(application: ApplicationCreate, db: Session = Depends(get_db)):
    db_application = Application(**application.model_dump())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

# Update application
@app.put("/applications/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int, 
    application: ApplicationUpdate, 
    db: Session = Depends(get_db)
):
    db_application = db.query(Application).filter(Application.id == application_id).first()
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    for key, value in application.model_dump().items():
        setattr(db_application, key, value)
    
    db.commit()
    db.refresh(db_application)
    return db_application

# Delete application
@app.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    db_application = db.query(Application).filter(Application.id == application_id).first()
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(db_application)
    db.commit()
    return None

# Export to Excel
@app.get("/export/excel")
def export_to_excel(db: Session = Depends(get_db)):
    applications = db.query(Application).order_by(Application.created_at.desc()).all()
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Applications"
    
    # Headers
    headers = [
        'ID', 'Company', 'Position', 'Location', 'Salary', 
        'Status', 'Date Applied', 'Deadline', 'Job URL', 'Notes'
    ]
    ws.append(headers)
    
    # Data rows
    for app in applications:
        ws.append([
            app.id,
            app.company_name,
            app.position_title,
            app.location or '',
            app.salary or '',
            app.status,
            app.date_applied.strftime('%Y-%m-%d') if app.date_applied else '',
            app.deadline.strftime('%Y-%m-%d') if app.deadline else '',
            app.job_url or '',
            app.notes or ''
        ])
    
    # Save to BytesIO
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=applications.xlsx"}
    )

if __name__ == "__main__":
    import uvicorn
    # This block allows running the app directly with `python main.py`
    # Best for development. For production, use a command like:
    # uvicorn app.main:app --host 0.0.0.0 --port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)