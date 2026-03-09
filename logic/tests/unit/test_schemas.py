"""
Unit tests for app/schemas.py

Tests Pydantic v2 validators: URL scheme validation, field length limits,
required fields, and optional field behaviour.
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    NoteCreate,
    NoteUpdate,
    DeadlineCreate,
    ScrapeRequest,
)


# ---------------------------------------------------------------------------
# ApplicationCreate / ApplicationBase validators
# ---------------------------------------------------------------------------

class TestApplicationCreateJobUrl:
    """job_url field validation — most important security-relevant schema test."""

    def test_accepts_https_url(self):
        a = ApplicationCreate(
            company_name="Stripe",
            position_title="SWE",
            job_url="https://stripe.com/jobs/1",
        )
        assert a.job_url == "https://stripe.com/jobs/1"

    def test_accepts_http_url(self):
        a = ApplicationCreate(
            company_name="Corp",
            position_title="Dev",
            job_url="http://jobs.example.com/1",
        )
        assert a.job_url == "http://jobs.example.com/1"

    def test_accepts_none_url(self):
        a = ApplicationCreate(company_name="Corp", position_title="Dev", job_url=None)
        assert a.job_url is None

    def test_rejects_javascript_scheme(self):
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                company_name="Corp",
                position_title="Dev",
                job_url="javascript:alert(document.cookie)",
            )
        errors = str(exc_info.value)
        assert "http or https" in errors

    def test_rejects_data_scheme(self):
        with pytest.raises(ValidationError):
            ApplicationCreate(
                company_name="Corp",
                position_title="Dev",
                job_url="data:text/html,<script>alert(1)</script>",
            )

    def test_rejects_ftp_scheme(self):
        with pytest.raises(ValidationError):
            ApplicationCreate(
                company_name="Corp",
                position_title="Dev",
                job_url="ftp://files.example.com/resume.pdf",
            )


class TestApplicationCreateRequiredFields:
    def test_rejects_missing_company_name(self):
        with pytest.raises(ValidationError):
            ApplicationCreate(position_title="Dev")

    def test_rejects_missing_position_title(self):
        with pytest.raises(ValidationError):
            ApplicationCreate(company_name="Corp")

    def test_rejects_company_name_over_255_chars(self):
        with pytest.raises(ValidationError):
            ApplicationCreate(company_name="x" * 256, position_title="Dev")

    def test_rejects_position_title_over_255_chars(self):
        with pytest.raises(ValidationError):
            ApplicationCreate(company_name="Corp", position_title="x" * 256)

    def test_status_defaults_to_applied(self):
        a = ApplicationCreate(company_name="Corp", position_title="Dev")
        assert a.status == "Applied"

    def test_optional_fields_default_to_none(self):
        a = ApplicationCreate(company_name="Corp", position_title="Dev")
        assert a.location is None
        assert a.salary is None
        assert a.job_url is None
        assert a.deadline is None


class TestApplicationUpdate:
    """ApplicationUpdate has the same job_url validator on an optional field."""

    def test_all_fields_optional(self):
        u = ApplicationUpdate()
        assert u.company_name is None
        assert u.status is None

    def test_rejects_javascript_url(self):
        with pytest.raises(ValidationError):
            ApplicationUpdate(job_url="javascript:void(0)")

    def test_accepts_https_url(self):
        u = ApplicationUpdate(job_url="https://careers.example.com/1")
        assert u.job_url == "https://careers.example.com/1"


# ---------------------------------------------------------------------------
# NoteCreate / NoteUpdate validators
# ---------------------------------------------------------------------------

class TestNoteCreate:
    def test_accepts_normal_content(self):
        n = NoteCreate(content="Spoke to recruiter on Friday.")
        assert n.content == "Spoke to recruiter on Friday."

    def test_accepts_content_at_max_length(self):
        n = NoteCreate(content="a" * 50_000)
        assert len(n.content) == 50_000

    def test_rejects_content_over_50000_chars(self):
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(content="a" * 50_001)
        assert "50000" in str(exc_info.value) or "max_length" in str(exc_info.value).lower()

    def test_rejects_missing_content(self):
        with pytest.raises(ValidationError):
            NoteCreate()


# ---------------------------------------------------------------------------
# DeadlineCreate validators
# ---------------------------------------------------------------------------

class TestDeadlineCreate:
    def test_accepts_valid_deadline(self):
        d = DeadlineCreate(
            deadline_type="Interview",
            deadline_date=datetime(2026, 3, 15, 10, 0, 0),
        )
        assert d.deadline_type == "Interview"
        assert d.is_completed is False

    def test_rejects_missing_deadline_type(self):
        with pytest.raises(ValidationError):
            DeadlineCreate(deadline_date=datetime(2026, 3, 15))

    def test_rejects_missing_deadline_date(self):
        with pytest.raises(ValidationError):
            DeadlineCreate(deadline_type="Application")

    def test_rejects_deadline_type_over_100_chars(self):
        with pytest.raises(ValidationError):
            DeadlineCreate(deadline_type="x" * 101, deadline_date=datetime(2026, 3, 15))


# ---------------------------------------------------------------------------
# ScrapeRequest validators
# ---------------------------------------------------------------------------

class TestScrapeRequest:
    def test_accepts_valid_http_url(self):
        r = ScrapeRequest(url="https://jobs.example.com/123")
        assert str(r.url).startswith("https://")

    def test_rejects_non_url_string(self):
        with pytest.raises(ValidationError):
            ScrapeRequest(url="not-a-url")

    def test_rejects_missing_url(self):
        with pytest.raises(ValidationError):
            ScrapeRequest()
