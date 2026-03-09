"""
Smoke / deployment tests.

These run against a LIVE deployment (not local). Set environment variables
before running:

    TARGET_URL=https://yourapi.onrender.com
    FRONTEND_URL=https://yourapp.pages.dev

Usage:
    TARGET_URL=https://api.example.com python -m pytest logic/tests/smoke/ -v

These tests do NOT require a DB, auth tokens, or mocks — they're pure HTTP probes.
"""
import os
import pytest
import httpx

BACKEND_URL = os.environ.get("PRODUCTION_API_URL", "").rstrip("/")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "").rstrip("/")


# ---------------------------------------------------------------------------
# Backend: Render deployment
# ---------------------------------------------------------------------------

@pytest.mark.smoke
class TestBackendHealth:
    @pytest.fixture(scope="class")
    def http(self):
        if not BACKEND_URL:
            pytest.skip("TARGET_URL not set — skipping backend smoke tests")
        with httpx.Client(base_url=BACKEND_URL, timeout=20.0) as client:
            yield client

    def test_health_endpoint_returns_200(self, http):
        r = http.get("/")
        assert r.status_code == 200

    def test_health_response_has_correct_status(self, http):
        data = http.get("/").json()
        assert data.get("status") == "running"

    def test_health_response_mentions_postgresql(self, http):
        data = http.get("/").json()
        assert "PostgreSQL" in data.get("database", "")

    def test_health_response_time_under_5_seconds(self, http):
        import time
        start = time.monotonic()
        http.get("/")
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"Health check took {elapsed:.1f}s — possible cold start"


@pytest.mark.smoke
class TestBackendAuthEnforcement:
    @pytest.fixture(scope="class")
    def http(self):
        if not BACKEND_URL:
            pytest.skip("TARGET_URL not set — skipping backend smoke tests")
        with httpx.Client(base_url=BACKEND_URL, timeout=20.0) as client:
            yield client

    def test_applications_without_token_returns_403(self, http):
        """Auth must be enforced on the live deployment — no regression allowed."""
        r = http.get("/applications")
        assert r.status_code == 403

    def test_scrape_without_token_is_rejected(self, http):
        r = http.post(
            "/scrape",
            json={"url": "https://example.com"},
            headers={"X-Gemini-Api-Key": "fake"},
        )
        assert r.status_code in (403, 422)

    def test_export_without_token_is_rejected(self, http):
        r = http.get("/export/excel")
        assert r.status_code == 403


@pytest.mark.smoke
class TestBackendCors:
    @pytest.fixture(scope="class")
    def http(self):
        if not BACKEND_URL:
            pytest.skip("TARGET_URL not set — skipping backend smoke tests")
        with httpx.Client(base_url=BACKEND_URL, timeout=20.0) as client:
            yield client

    def test_cors_headers_present_on_preflight(self, http):
        r = http.options(
            "/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS should allow localhost origins (for local dev to work)
        assert r.status_code in (200, 204)
        assert "access-control-allow-origin" in r.headers


# ---------------------------------------------------------------------------
# Frontend: Cloudflare Pages deployment
# ---------------------------------------------------------------------------

@pytest.mark.smoke
class TestFrontendAvailability:
    @pytest.fixture(scope="class")
    def http(self):
        if not FRONTEND_URL:
            pytest.skip("FRONTEND_URL not set — skipping frontend smoke tests")
        with httpx.Client(timeout=20.0) as client:
            yield client

    def test_frontend_homepage_returns_200(self, http):
        r = http.get(FRONTEND_URL)
        assert r.status_code == 200

    def test_frontend_returns_html(self, http):
        r = http.get(FRONTEND_URL)
        content_type = r.headers.get("content-type", "")
        assert "text/html" in content_type

    def test_frontend_response_is_not_a_server_error(self, http):
        r = http.get(FRONTEND_URL)
        assert r.status_code < 500

    def test_frontend_html_contains_react_root(self, http):
        r = http.get(FRONTEND_URL)
        assert 'id="root"' in r.text or "<div" in r.text

    def test_frontend_response_time_under_5_seconds(self, http):
        import time
        start = time.monotonic()
        http.get(FRONTEND_URL)
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"Frontend took {elapsed:.1f}s to respond"
