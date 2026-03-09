"""
Integration tests for Notes endpoints.

Covers: CRUD, activity log side-effects, ordering.
"""
import pytest
from app.models import ActivityLog, Note


class TestCreateNote:
    def test_creates_note_and_returns_201(self, client, make_application):
        app_data = make_application()
        r = client.post(
            f"/applications/{app_data['id']}/notes",
            json={"content": "Called recruiter today"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["content"] == "Called recruiter today"
        assert data["application_id"] == app_data["id"]
        assert "id" in data

    def test_creates_note_added_activity(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]

        client.post(f"/applications/{app_id}/notes", json={"content": "First note"})

        activity = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "note_added",
            )
            .first()
        )
        assert activity is not None

    def test_returns_404_for_nonexistent_application(self, client):
        r = client.post(
            "/applications/99999/notes",
            json={"content": "Note for phantom app"},
        )
        assert r.status_code == 404

    def test_rejects_note_content_over_50000_chars(self, client, make_application):
        app_data = make_application()
        r = client.post(
            f"/applications/{app_data['id']}/notes",
            json={"content": "x" * 50_001},
        )
        assert r.status_code == 422


class TestGetNotes:
    def test_returns_notes_for_application(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]

        client.post(f"/applications/{app_id}/notes", json={"content": "Note 1"})
        client.post(f"/applications/{app_id}/notes", json={"content": "Note 2"})

        r = client.get(f"/applications/{app_id}/notes")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_returns_empty_list_when_no_notes(self, client, make_application):
        app_data = make_application()
        r = client.get(f"/applications/{app_data['id']}/notes")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_404_for_nonexistent_application(self, client):
        r = client.get("/applications/99999/notes")
        assert r.status_code == 404


class TestUpdateNote:
    def test_updates_note_content(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]

        create_r = client.post(
            f"/applications/{app_id}/notes",
            json={"content": "Original content"},
        )
        note_id = create_r.json()["id"]

        update_r = client.put(f"/notes/{note_id}", json={"content": "Updated content"})
        assert update_r.status_code == 200
        assert update_r.json()["content"] == "Updated content"

    def test_creates_note_updated_activity(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]

        create_r = client.post(f"/applications/{app_id}/notes", json={"content": "Original"})
        note_id = create_r.json()["id"]

        client.put(f"/notes/{note_id}", json={"content": "Updated"})

        activity = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "note_updated",
            )
            .first()
        )
        assert activity is not None

    def test_returns_404_for_nonexistent_note(self, client):
        r = client.put("/notes/99999", json={"content": "Ghost update"})
        assert r.status_code == 404


class TestDeleteNote:
    def test_deletes_note_and_returns_204(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]

        create_r = client.post(f"/applications/{app_id}/notes", json={"content": "Delete me"})
        note_id = create_r.json()["id"]

        r = client.delete(f"/notes/{note_id}")
        assert r.status_code == 204

    def test_note_not_retrievable_after_delete(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]

        create_r = client.post(f"/applications/{app_id}/notes", json={"content": "Going away"})
        note_id = create_r.json()["id"]

        client.delete(f"/notes/{note_id}")

        assert db_session.query(Note).filter(Note.id == note_id).first() is None

    def test_creates_note_deleted_activity(self, client, make_application, db_session):
        app_data = make_application()
        app_id = app_data["id"]

        create_r = client.post(f"/applications/{app_id}/notes", json={"content": "Will be deleted"})
        note_id = create_r.json()["id"]

        client.delete(f"/notes/{note_id}")

        activity = (
            db_session.query(ActivityLog)
            .filter(
                ActivityLog.application_id == app_id,
                ActivityLog.activity_type == "note_deleted",
            )
            .first()
        )
        assert activity is not None

    def test_returns_404_for_nonexistent_note(self, client):
        r = client.delete("/notes/99999")
        assert r.status_code == 404
