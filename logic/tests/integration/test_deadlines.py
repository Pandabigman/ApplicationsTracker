"""
Integration tests for Deadline endpoints.

Covers: CRUD, completion toggle activity log, ordering.
"""
import pytest
from app.models import ActivityLog, Deadline


SAMPLE_DEADLINE = {
    "deadline_type": "Application",
    "deadline_date": "2026-06-01T12:00:00",
}


class TestCreateDeadline:
    def test_creates_deadline_and_returns_201(self, client, make_application):
        app_data = make_application()
        r = client.post(
            f"/applications/{app_data['id']}/deadlines",
            json=SAMPLE_DEADLINE,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["deadline_type"] == "Application"
        assert data["is_completed"] is False
        assert data["application_id"] == app_data["id"]

    def test_creates_deadline_added_activity(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]

        client.post(f"/applications/{app_id}/deadlines", json=SAMPLE_DEADLINE)

        activity = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "deadline_added",
            )
            .first()
        )
        assert activity is not None

    def test_returns_404_for_nonexistent_application(self, client):
        r = client.post("/applications/99999/deadlines", json=SAMPLE_DEADLINE)
        assert r.status_code == 404

    def test_rejects_missing_deadline_type(self, client, make_application):
        app_data = make_application()
        r = client.post(
            f"/applications/{app_data['id']}/deadlines",
            json={"deadline_date": "2026-06-01T12:00:00"},
        )
        assert r.status_code == 422


class TestGetDeadlines:
    def test_returns_deadlines_for_application(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]

        client.post(f"/applications/{app_id}/deadlines", json={
            "deadline_type": "Application",
            "deadline_date": "2026-07-01T12:00:00",
        })
        client.post(f"/applications/{app_id}/deadlines", json={
            "deadline_type": "Interview",
            "deadline_date": "2026-06-01T12:00:00",
        })

        r = client.get(f"/applications/{app_id}/deadlines")
        assert r.status_code == 200
        deadlines = r.json()
        assert len(deadlines) == 2
        # Should be ordered by deadline_date ASC
        assert deadlines[0]["deadline_type"] == "Interview"  # June before July

    def test_returns_empty_list_when_no_deadlines(self, client, make_application):
        app_data = make_application()
        r = client.get(f"/applications/{app_data['id']}/deadlines")
        assert r.status_code == 200
        assert r.json() == []


class TestUpdateDeadline:
    def _create_deadline(self, client, app_id, **kwargs):
        payload = {**SAMPLE_DEADLINE, **kwargs}
        r = client.post(f"/applications/{app_id}/deadlines", json=payload)
        assert r.status_code == 201
        return r.json()

    def test_can_mark_deadline_as_completed(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]
        deadline = self._create_deadline(client, app_id)
        deadline_id = deadline["id"]

        r = client.put(f"/deadlines/{deadline_id}", json={"is_completed": True})
        assert r.status_code == 200
        assert r.json()["is_completed"] is True

    def test_completing_deadline_creates_activity(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]
        deadline = self._create_deadline(client, app_id)

        client.put(f"/deadlines/{deadline['id']}", json={"is_completed": True})

        activity = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "deadline_completed",
            )
            .first()
        )
        assert activity is not None

    def test_reopening_deadline_creates_activity(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]
        deadline = self._create_deadline(client, app_id)
        deadline_id = deadline["id"]

        # Complete then reopen
        client.put(f"/deadlines/{deadline_id}", json={"is_completed": True})
        client.put(f"/deadlines/{deadline_id}", json={"is_completed": False})

        activity = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "deadline_reopened",
            )
            .first()
        )
        assert activity is not None

    def test_no_activity_when_is_completed_not_changed(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]
        deadline = self._create_deadline(client, app_id)

        # Update description only — is_completed stays False
        client.put(f"/deadlines/{deadline['id']}", json={"description": "Updated description"})

        completed_activities = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "deadline_completed",
            )
            .all()
        )
        assert len(completed_activities) == 0

    def test_returns_404_for_nonexistent_deadline(self, client):
        r = client.put("/deadlines/99999", json={"is_completed": True})
        assert r.status_code == 404


class TestDeleteDeadline:
    def test_deletes_deadline_and_returns_204(self, client, make_application):
        app_data = make_application()
        r = client.post(
            f"/applications/{app_data['id']}/deadlines",
            json=SAMPLE_DEADLINE,
        )
        deadline_id = r.json()["id"]

        delete_r = client.delete(f"/deadlines/{deadline_id}")
        assert delete_r.status_code == 204

    def test_deadline_not_in_db_after_delete(self, client, make_application, db_session):
        app_data = make_application()
        r = client.post(
            f"/applications/{app_data['id']}/deadlines",
            json=SAMPLE_DEADLINE,
        )
        deadline_id = r.json()["id"]

        client.delete(f"/deadlines/{deadline_id}")

        assert db_session.query(Deadline).filter(Deadline.id == deadline_id).first() is None

    def test_creates_deadline_deleted_activity(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]
        r = client.post(f"/applications/{app_id}/deadlines", json=SAMPLE_DEADLINE)
        deadline_id = r.json()["id"]

        client.delete(f"/deadlines/{deadline_id}")

        activity = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "deadline_deleted",
            )
            .first()
        )
        assert activity is not None

    def test_returns_404_for_nonexistent_deadline(self, client):
        r = client.delete("/deadlines/99999")
        assert r.status_code == 404
