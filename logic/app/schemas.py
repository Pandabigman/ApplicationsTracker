from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime, date

class ApplicationBase(BaseModel):
    company_name: str
    position_title: str
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    status: Optional[str] = 'Applied'
    deadline: Optional[date] = None
    notes: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    date_applied: Optional[datetime] = None

class ApplicationUpdate(ApplicationBase):
    pass

class ApplicationResponse(ApplicationBase):
    id: int
    date_applied: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ScrapeRequest(BaseModel):
    url: str

class ScrapeResponse(BaseModel):
    company_name: Optional[str] = None
    position_title: Optional[str] = None
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
