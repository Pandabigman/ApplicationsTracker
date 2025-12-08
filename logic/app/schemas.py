from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ============== Application Schemas ==============

class ApplicationBase(BaseModel):
    company_name: str
    position_title: str
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    status: Optional[str] = 'Applied'
    deadline: Optional[datetime] = None

class ApplicationCreate(ApplicationBase):
    date_applied: Optional[datetime] = None

class ApplicationUpdate(BaseModel):
    company_name: Optional[str] = None
    position_title: Optional[str] = None
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[datetime] = None

class ApplicationResponse(ApplicationBase):
    id: int
    date_applied: datetime
    created_at: datetime
    updated_at: datetime
    notes: Optional[List['NoteResponse']] = []
    activities: Optional[List['ActivityLogResponse']] = []
    deadlines: Optional[List['DeadlineResponse']] = []
    job_details: Optional['JobDetailResponse'] = None

    class Config:
        from_attributes = True


# ============== JobDetail Schemas ==============

class JobDetailBase(BaseModel):
    description: Optional[str] = None
    requirements: Optional[str] = None
    clean_text_content: Optional[str] = None
    ai_thoughts: Optional[str] = None

class JobDetailCreate(JobDetailBase):
    application_id: int

class JobDetailUpdate(JobDetailBase):
    pass

class JobDetailResponse(JobDetailBase):
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Note Schemas ==============

class NoteBase(BaseModel):
    content: str

class NoteCreate(NoteBase):
    application_id: int

class NoteUpdate(NoteBase):
    pass

class NoteResponse(NoteBase):
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== ActivityLog Schemas ==============

class ActivityLogBase(BaseModel):
    activity_type: str
    description: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None

class ActivityLogCreate(ActivityLogBase):
    application_id: int

class ActivityLogResponse(ActivityLogBase):
    id: int
    application_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Deadline Schemas ==============

class DeadlineBase(BaseModel):
    deadline_type: str  # application, interview, assessment, follow_up, etc.
    deadline_date: datetime
    description: Optional[str] = None
    is_completed: bool = False

class DeadlineCreate(DeadlineBase):
    application_id: int

class DeadlineUpdate(BaseModel):
    deadline_type: Optional[str] = None
    deadline_date: Optional[datetime] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None

class DeadlineResponse(DeadlineBase):
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Scraping Schemas ==============

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
    clean_text_content: Optional[str] = None
    ai_thoughts: Optional[str] = None
    application_deadline: Optional[str] = None


# Resolve forward references
ApplicationResponse.model_rebuild()
