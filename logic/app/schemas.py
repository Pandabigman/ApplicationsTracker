from pydantic import AnyHttpUrl, BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

# ============== Application Schemas ==============


class ApplicationBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    position_title: str = Field(..., max_length=255)
    job_url: Optional[str] = Field(None, max_length=2048)
    location: Optional[str] = Field(None, max_length=255)
    salary: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field("Applied", max_length=100)
    deadline: Optional[datetime] = None

    @field_validator("job_url")
    @classmethod
    def job_url_must_be_http(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            from urllib.parse import urlparse
            parsed = urlparse(v)
            if parsed.scheme not in ("http", "https"):
                raise ValueError("job_url must use http or https")
        except Exception:
            raise ValueError("job_url must be a valid http/https URL")
        return v


class ApplicationCreate(ApplicationBase):
    date_applied: Optional[datetime] = None


class ApplicationUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=255)
    position_title: Optional[str] = Field(None, max_length=255)
    job_url: Optional[str] = Field(None, max_length=2048)
    location: Optional[str] = Field(None, max_length=255)
    salary: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=100)
    deadline: Optional[datetime] = None

    @field_validator("job_url")
    @classmethod
    def job_url_must_be_http(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            from urllib.parse import urlparse
            parsed = urlparse(v)
            if parsed.scheme not in ("http", "https"):
                raise ValueError("job_url must use http or https")
        except Exception:
            raise ValueError("job_url must be a valid http/https URL")
        return v


class ApplicationResponse(ApplicationBase):
    id: int
    date_applied: datetime
    created_at: datetime
    updated_at: datetime
    notes: Optional[List["NoteResponse"]] = []
    activities: Optional[List["ActivityLogResponse"]] = []
    deadlines: Optional[List["DeadlineResponse"]] = []
    job_details: Optional["JobDetailResponse"] = None

    class Config:
        from_attributes = True


# ============== JobDetail Schemas ==============


class JobDetailBase(BaseModel):
    description: Optional[str] = None
    requirements: Optional[str] = None
    clean_text_content: Optional[str] = None
    ai_thoughts: Optional[str] = None


class JobDetailCreate(JobDetailBase):
    pass


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
    content: str = Field(..., max_length=50_000)


class NoteCreate(NoteBase):
    pass


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
    deadline_type: str = Field(..., max_length=100)
    deadline_date: datetime
    description: Optional[str] = Field(None, max_length=1000)
    is_completed: bool = False


class DeadlineCreate(DeadlineBase):
    pass


class DeadlineUpdate(BaseModel):
    deadline_type: Optional[str] = Field(None, max_length=100)
    deadline_date: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=1000)
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
    url: AnyHttpUrl


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
