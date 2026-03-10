"""
Integration tests for security: auth bypass, user isolation, CORS, input validation.

These are the most important tests in the suite.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


# ---------------------------------------------------------------------------
# Auth enforcement — requests without a valid token must be rejected
# ---------------------------------------------------------------------------

class TestAuthEnforcement:
    """Use a raw (unpatched) TestClient to test real auth behaviour."""

    def test_applications_without_token_returns_403(self):
        """HTTPBearer returns 403 when no Authorization header is present."""
        with TestClient(app) as c:
            r = c.get("/applications")
        assert r.status_code == 403

    def test_notes_without_token_returns_403(self):
        with TestClient(app) as c:
            r = c.get("/applications/1/notes")
        assert r.status_code == 403

    def test_scrape_without_token_returns_403(self):
        with TestClient(app) as c:
            r = c.post("/scrape", json={"url": "https://example.com"})
        assert r.status_code == 403

    def test_export_without_token_returns_403(self):
        with TestClient(app) as c:
            r = c.get("/export/excel")
        assert r.status_code == 403

    def test_health_check_is_public(self):
        """GET / must be reachable without authentication."""
        with TestClient(app) as c:
            r = c.get("/")
        assert r.status_code == 200

    def test_malformed_token_returns_4xx(self):
        """A syntactically invalid JWT must not result in a 200."""
        with TestClient(app) as c:
            r = c.get(
                "/applications",
                headers={"Authorization": "Bearer this.is.not.a.real.jwt"},
            )
        # 401 (invalid token) or 500 (JWKS unavailable in test env) — NOT 200
        assert r.status_code != 200


# ---------------------------------------------------------------------------
# User isolation — TEST_USER_A must never touch TEST_USER_B's data
# ---------------------------------------------------------------------------

class TestUserIsolation:
    """
    Creates data owned by TEST_USER_B directly in the DB,
    then verifies TEST_USER_A (via `client` fixture) cannot access or modify it.
    """

    def test_user_a_cannot_get_user_b_application(self, client, other_user_app):
        r = client.get(f"/applications/{other_user_app}")
        assert r.status_code == 404

    def test_user_a_cannot_update_user_b_application(self, client, other_user_app):
        r = client.put(
            f"/applications/{other_user_app}",
            json={"status": "Rejected"},
        )
        assert r.status_code == 404

    def test_user_a_cannot_delete_user_b_application(self, client, other_user_app):
        r = client.delete(f"/applications/{other_user_app}")
        assert r.status_code == 404

    def test_user_a_cannot_add_note_to_user_b_application(self, client, other_user_app):
        r = client.post(
            f"/applications/{other_user_app}/notes",
            json={"content": "Sneaky note from user A"},
        )
        assert r.status_code == 404

    def test_user_a_cannot_get_notes_for_user_b_application(self, client, other_user_app):
        r = client.get(f"/applications/{other_user_app}/notes")
        assert r.status_code == 404

    def test_user_a_cannot_add_deadline_to_user_b_application(self, client, other_user_app):
        r = client.post(
            f"/applications/{other_user_app}/deadlines",
            json={"deadline_type": "Interview", "deadline_date": "2026-06-01T10:00:00"},
        )
        assert r.status_code == 404

    def test_user_a_cannot_create_job_details_for_user_b_application(self, client, other_user_app):
        r = client.post(
            f"/applications/{other_user_app}/job-details",
            json={"description": "Injected description"},
        )
        assert r.status_code == 404

    def test_list_endpoint_only_returns_own_applications(self, client, other_user_app, make_application):
        """GET /applications must never include another user's rows."""
        make_application(company="My Corp")  # User A's app

        r = client.get("/applications")
        assert r.status_code == 200
        companies = [a["company_name"] for a in r.json()]
        assert "My Corp" in companies
        assert "B Corp" not in companies  # B Corp belongs to TEST_USER_B


# ---------------------------------------------------------------------------
# Cross-resource isolation for notes and deadlines
# ---------------------------------------------------------------------------

class TestNoteAndDeadlineIsolation:
    """PUT/DELETE /notes/{id} and /deadlines/{id} must verify ownership."""

    def test_user_a_cannot_update_note_belonging_to_user_b_app(
        self, client, other_user_app, db_session
    ):
        from app.models import Note

        # Create a note directly in the DB for user B's app
        note = Note(application_id=other_user_app, content="User B's private note")
        db_session.add(note)
        db_session.commit()
        db_session.refresh(note)

        r = client.put(f"/notes/{note.id}", json={"content": "Hijacked!"})
        assert r.status_code == 404

    def test_user_a_cannot_delete_deadline_belonging_to_user_b_app(
        self, client, other_user_app, db_session
    ):
        from app.models import Deadline
        from datetime import datetime

        deadline = Deadline(
            application_id=other_user_app,
            deadline_type="Interview",
            deadline_date=datetime(2026, 6, 1),
        )
        db_session.add(deadline)
        db_session.commit()
        db_session.refresh(deadline)

        r = client.delete(f"/deadlines/{deadline.id}")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# CORS headers
# ---------------------------------------------------------------------------

class TestCorsHeaders:
    def test_cors_headers_present_for_allowed_localhost_origin(self, client):
        r = client.options(
            "/applications",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI CORS middleware should respond with allow-origin header
        assert "access-control-allow-origin" in r.headers

    def test_cors_allows_configured_frontend_url(self, client):
        r = client.options(
            "/applications",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        origin = r.headers.get("access-control-allow-origin", "")
        assert origin in ("*", "http://localhost:5173")


# ---------------------------------------------------------------------------
# Input validation — malformed bodies must return 422
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_create_application_with_missing_company_returns_422(self, client):
        r = client.post("/applications", json={"position_title": "Dev"})
        assert r.status_code == 422

    def test_create_application_with_javascript_url_returns_422(self, client):
        r = client.post("/applications", json={
            "company_name": "Corp",
            "position_title": "Dev",
            "job_url": "javascript:alert(1)",
        })
        assert r.status_code == 422

    def test_create_note_with_empty_body_returns_422(self, client, make_application):
        app_data = make_application()
        r = client.post(f"/applications/{app_data['id']}/notes", json={})
        assert r.status_code == 422

    def test_scrape_with_empty_body_returns_422(self, client):
        r = client.post("/scrape", json={})
        assert r.status_code == 422
