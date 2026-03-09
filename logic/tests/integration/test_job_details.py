"""
Integration tests for JobDetails endpoints (1:1 with Application).
"""
import pytest


SAMPLE_JOB_DETAIL = {
    "description": "Build infrastructure for AI products",
    "requirements": "5+ years Python, strong ML background",
    "ai_thoughts": "Focus on distributed systems and safety work",
    "clean_text_content": "Senior ML Engineer at Anthropic...",
}


class TestCreateJobDetails:
    def test_creates_job_details_and_returns_201(self, client, make_application):
        app_data = make_application()
        r = client.post(
            f"/applications/{app_data['id']}/job-details",
            json=SAMPLE_JOB_DETAIL,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["description"] == "Build infrastructure for AI products"
        assert data["requirements"] == "5+ years Python, strong ML background"
        assert data["application_id"] == app_data["id"]

    def test_rejects_duplicate_job_details(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]

        client.post(f"/applications/{app_id}/job-details", json=SAMPLE_JOB_DETAIL)
        r = client.post(f"/applications/{app_id}/job-details", json={"description": "Second attempt"})

        assert r.status_code == 400
        assert "already exist" in r.json()["detail"].lower()

    def test_returns_404_for_nonexistent_application(self, client):
        r = client.post("/applications/99999/job-details", json=SAMPLE_JOB_DETAIL)
        assert r.status_code == 404

    def test_accepts_all_optional_fields_null(self, client, make_application):
        app_data = make_application()
        r = client.post(
            f"/applications/{app_data['id']}/job-details",
            json={},
        )
        assert r.status_code == 201

    def test_job_details_appear_in_application_response(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]

        client.post(f"/applications/{app_id}/job-details", json=SAMPLE_JOB_DETAIL)

        r = client.get(f"/applications/{app_id}")
        assert r.status_code == 200
        job_details = r.json().get("job_details")
        assert job_details is not None
        assert job_details["description"] == "Build infrastructure for AI products"


class TestUpdateJobDetails:
    def test_updates_job_details(self, client, make_application):
        app_data = make_application()
        app_id = app_data["id"]

        client.post(f"/applications/{app_id}/job-details", json=SAMPLE_JOB_DETAIL)
        r = client.put(
            f"/applications/{app_id}/job-details",
            json={"description": "Updated description"},
        )

        assert r.status_code == 200
        assert r.json()["description"] == "Updated description"

    def test_returns_404_when_no_job_details_exist(self, client, make_application):
        app_data = make_application()
        r = client.put(
            f"/applications/{app_data['id']}/job-details",
            json={"description": "Update with no existing details"},
        )
        assert r.status_code == 404

    def test_returns_404_for_nonexistent_application(self, client):
        r = client.put("/applications/99999/job-details", json={"description": "x"})
        assert r.status_code == 404
