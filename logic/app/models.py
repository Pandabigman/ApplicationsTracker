from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    position_title = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    salary = Column(String(100), nullable=True)
    job_url = Column(Text, nullable=True)
    status = Column(String(50), default='Applied', nullable=False, index=True)
    date_applied = Column(DateTime, server_default=func.now())
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    job_details = relationship("JobDetail", back_populates="application", uselist=False, cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="application", cascade="all, delete-orphan", order_by="Note.created_at.desc()")
    activities = relationship("ActivityLog", back_populates="application", cascade="all, delete-orphan", order_by="ActivityLog.created_at.desc()")
    deadlines = relationship("Deadline", back_populates="application", cascade="all, delete-orphan", order_by="Deadline.deadline_date.asc()")

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'position_title': self.position_title,
            'job_url': self.job_url,
            'location': self.location,
            'salary': self.salary,
            'status': self.status,
            'date_applied': self.date_applied.isoformat() if self.date_applied else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class JobDetail(Base):
    __tablename__ = "job_details"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    clean_text_content = Column(Text, nullable=True)  # Store cleaned text from HTML
    ai_thoughts = Column(Text, nullable=True)  # AI-generated advice on how to stand out
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    application = relationship("Application", back_populates="job_details")

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'description': self.description,
            'requirements': self.requirements,
            'clean_text_content': self.clean_text_content,
            'ai_thoughts': self.ai_thoughts,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    application = relationship("Application", back_populates="notes")

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)  # status_change, interview, note, deadline_set, etc.
    description = Column(Text, nullable=True)
    old_value = Column(Text, nullable=True)  # For tracking changes (e.g., old status)
    new_value = Column(Text, nullable=True)  # New value
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    application = relationship("Application", back_populates="activities")

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Deadline(Base):
    __tablename__ = "deadlines"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), nullable=False, index=True)
    deadline_type = Column(String(50), nullable=False)  # application, interview, assessment, follow_up, etc.
    deadline_date = Column(DateTime, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_completed = Column(Integer, default=0)  # 0 = pending, 1 = completed (SQLite doesn't have boolean)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    application = relationship("Application", back_populates="deadlines")

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'deadline_type': self.deadline_type,
            'deadline_date': self.deadline_date.isoformat() if self.deadline_date else None,
            'description': self.description,
            'is_completed': bool(self.is_completed),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
