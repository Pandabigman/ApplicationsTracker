from sqlalchemy import Column, Integer, String, Text, DateTime, Date
from sqlalchemy.sql import func
from database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    position_title = Column(String(255), nullable=False)
    job_url = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    salary = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    status = Column(String(50), default='Applied', nullable=False)
    date_applied = Column(DateTime(timezone=True), server_default=func.now())
    deadline = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'position_title': self.position_title,
            'job_url': self.job_url,
            'location': self.location,
            'salary': self.salary,
            'description': self.description,
            'requirements': self.requirements,
            'status': self.status,
            'date_applied': self.date_applied.isoformat() if self.date_applied else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
