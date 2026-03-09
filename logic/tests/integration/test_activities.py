"""
Integration tests for Activity Log endpoint.
"""
import pytest


class TestGetActivities:
    def test_returns_activity_log_for_application(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]

        r = client.get(f"/applications/{app_id}/activities")
        assert r.status_code == 200
        activities = r.json()
        # At minimum, application_created was logged on creation
        assert len(activities) >= 1
        assert any(a["activity_type"] == "application_created" for a in activities)

    def test_activities_include_status_changes(self, client, make_application):
        app_data = make_application(status="Applied")
        app_id = app_data["id"]

        client.put(f"/applications/{app_id}", json={"status": "Interview"})

        r = client.get(f"/applications/{app_id}/activities")
        activities = r.json()
        status_changes = [a for a in activities if a["activity_type"] == "status_change"]
        assert len(status_changes) == 1
        assert status_changes[0]["old_value"] == "Applied"
        assert status_changes[0]["new_value"] == "Interview"

    def test_activities_include_note_events(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]

        create_r = client.post(f"/applications/{app_id}/notes", json={"content": "First note"})
        note_id = create_r.json()["id"]
        client.put(f"/notes/{note_id}", json={"content": "Updated note"})
        client.delete(f"/notes/{note_id}")

        r = client.get(f"/applications/{app_id}/activities")
        types = {a["activity_type"] for a in r.json()}
        assert "note_added" in types
        assert "note_updated" in types
        assert "note_deleted" in types

    def test_returns_404_for_nonexistent_application(self, client):
        r = client.get("/applications/99999/activities")
        assert r.status_code == 404

    def test_activities_have_required_fields(self, client, make_application):
        app_data = make_application()
        r = client.get(f"/applications/{app_data['id']}/activities")
        for activity in r.json():
            assert "id" in activity
            assert "activity_type" in activity
            assert "created_at" in activity
            assert "application_id" in activity
