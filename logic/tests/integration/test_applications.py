"""
Integration tests for Application CRUD endpoints.

Covers: creation, retrieval, update (including status-change activity log),
deletion with cascade verification.
"""
import pytest
from app.models import ActivityLog, Application


class TestCreateApplication:
    def test_returns_201_with_correct_fields(self, client):
        r = client.post("/applications", json={
            "company_name": "DeepMind",
            "position_title": "Research Engineer",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["company_name"] == "DeepMind"
        assert data["position_title"] == "Research Engineer"
        assert data["status"] == "Applied"  # default
        assert "id" in data
        assert "date_applied" in data

    def test_creates_activity_log_entry_on_creation(self, client, db_session):
        r = client.post("/applications", json={
            "company_name": "Anthropic",
            "position_title": "ML Engineer",
        })
        app_id = r.json()["id"]

        activities = (
            db_session.query(ActivityLog)
            .filter(ActivityLog.application_id == app_id)
            .all()
        )
        assert len(activities) == 1
        assert activities[0].activity_type == "application_created"
        assert activities[0].new_value == "Applied"

    def test_accepts_custom_status(self, client):
        r = client.post("/applications", json={
            "company_name": "Corp",
            "position_title": "Dev",
            "status": "Interview",
        })
        assert r.json()["status"] == "Interview"

    def test_accepts_optional_fields(self, client):
        r = client.post("/applications", json={
            "company_name": "OpenAI",
            "position_title": "Engineer",
            "location": "San Francisco",
            "salary": "$200k",
            "job_url": "https://openai.com/careers/1",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["location"] == "San Francisco"
        assert data["salary"] == "$200k"

    def test_rejects_missing_company_name(self, client):
        r = client.post("/applications", json={"position_title": "Dev"})
        assert r.status_code == 422

    def test_rejects_javascript_job_url(self, client):
        r = client.post("/applications", json={
            "company_name": "Corp",
            "position_title": "Dev",
            "job_url": "javascript:alert(document.cookie)",
        })
        assert r.status_code == 422


class TestGetApplications:
    def test_returns_empty_list_for_new_user(self, client):
        r = client.get("/applications")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_all_user_applications(self, client, make_application):
        make_application(company="Corp A")
        make_application(company="Corp B")

        r = client.get("/applications")
        assert r.status_code == 200
        companies = {a["company_name"] for a in r.json()}
        assert "Corp A" in companies
        assert "Corp B" in companies

    def test_returns_applications_ordered_newest_first(self, client, make_application):
        make_application(company="First Corp")
        make_application(company="Second Corp")

        r = client.get("/applications")
        companies = [a["company_name"] for a in r.json()]
        # Most recently created should be first
        assert companies[0] == "Second Corp"


class TestGetSingleApplication:
    def test_returns_application_with_related_data(self, client, make_application):
        app_data = make_application()
        r = client.get(f"/applications/{app_data['id']}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == app_data["id"]
        assert "notes" in data
        assert "activities" in data
        assert "deadlines" in data

    def test_returns_404_for_nonexistent_id(self, client):
        r = client.get("/applications/99999")
        assert r.status_code == 404


class TestUpdateApplication:
    def test_updates_fields(self, client, make_application):
        app_data = make_application(company="Old Corp")
        r = client.put(
            f"/applications/{app_data['id']}",
            json={"company_name": "New Corp"},
        )
        assert r.status_code == 200
        assert r.json()["company_name"] == "New Corp"

    def test_status_change_creates_activity_log(self, client, make_application, db_session):
        app_data = make_application(status="Applied")
        app_id = app_data["id"]

        client.put(f"/applications/{app_id}", json={"status": "Interview"})

        activity = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "status_change",
            )
            .first()
        )
        assert activity is not None
        assert activity.old_value == "Applied"
        assert activity.new_value == "Interview"

    def test_no_activity_log_when_status_unchanged(self, client, make_application, db_session):
        app_data = make_application(status="Applied")
        app_id = app_data["id"]

        # Update location only — no status change
        client.put(f"/applications/{app_id}", json={"location": "London"})

        status_activities = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "status_change",
            )
            .all()
        )
        assert len(status_activities) == 0

    def test_returns_404_for_nonexistent_id(self, client):
        r = client.put("/applications/99999", json={"status": "Rejected"})
        assert r.status_code == 404

    def test_partial_update_leaves_other_fields_unchanged(self, client, make_application):
        app_data = make_application(company="Corp", position="Eng", location="Berlin")
        app_id = app_data["id"]

        client.put(f"/applications/{app_id}", json={"status": "Rejected"})

        r = client.get(f"/applications/{app_id}")
        assert r.json()["location"] == "Berlin"
        assert r.json()["company_name"] == "Corp"


class TestDeleteApplication:
    def test_returns_204(self, client, make_application):
        app_data = make_application()
        r = client.delete(f"/applications/{app_data['id']}")
        assert r.status_code == 204

    def test_application_not_found_after_delete(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]
        client.delete(f"/applications/{app_id}")
        r = client.get(f"/applications/{app_id}")
        assert r.status_code == 404

    def test_delete_removes_associated_notes(self, client, make_application, db_session):
        from app.models import Note

        app_data = make_application()
        app_id = app_data["id"]

        # Create a note
        client.post(f"/applications/{app_id}/notes", json={"content": "Test note"})

        # Delete the application
        client.delete(f"/applications/{app_id}")

        # Note should also be gone (cascade delete)
        notes = db_session.query(Note).filter(Note.application_id == app_id).all()
        assert len(notes) == 0

    def test_delete_removes_associated_activities(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]

        client.delete(f"/applications/{app_id}")

        activities = (
            db_session.query(ActivityLog)
            .filter(ActivityLog.application_id == app_id)
            .all()
        )
        assert len(activities) == 0

    def test_returns_404_for_nonexistent_id(self, client):
        r = client.delete("/applications/99999")
        assert r.status_code == 404
