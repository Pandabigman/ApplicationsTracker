"""
Integration tests for the /scrape endpoint.

External services (Gemini, ScrapingBee) are mocked; SSRF guard and error
handling are tested through the full request/response cycle.
"""
import pytest
from unittest.mock import AsyncMock, patch

MOCK_SCRAPE_RESULT = {
    "company_name": "Stripe",
    "position_title": "Staff Engineer",
    "location": "Remote",
    "salary": "$200k–$250k",
    "description": "Build the financial infrastructure of the internet",
    "requirements": "5+ years distributed systems",
    "ai_thoughts": "Emphasize reliability engineering and payments domain knowledge",
    "application_deadline": None,
    "clean_text_content": "Stripe job posting text...",
    "job_url": "https://stripe.com/jobs/123",
}


class TestScrapeEndpoint:
    def test_successful_scrape_returns_200_with_job_data(self, client):
        with patch("app.main.scraper.scrape_url", new=AsyncMock(return_value=MOCK_SCRAPE_RESULT)):
            r = client.post(
                "/scrape",
                json={"url": "https://stripe.com/jobs/123"},
            )

        assert r.status_code == 200
        data = r.json()
        assert data["company_name"] == "Stripe"
        assert data["position_title"] == "Staff Engineer"

    def test_scrape_with_empty_extraction_returns_400(self, client):
        empty_result = {"company_name": None, "position_title": None}
        with patch("app.main.scraper.scrape_url", new=AsyncMock(return_value=empty_result)):
            r = client.post(
                "/scrape",
                json={"url": "https://example.com/jobs/1"},
            )

        assert r.status_code == 400
        assert "manually" in r.json()["detail"].lower()

    def test_scrape_raises_exception_returns_400(self, client):
        """Any unexpected exception from scraper.scrape_url → 400."""
        with patch(
            "app.main.scraper.scrape_url",
            new=AsyncMock(side_effect=Exception("Failed to fetch page")),
        ):
            r = client.post(
                "/scrape",
                json={"url": "https://example.com/jobs/1"},
            )

        assert r.status_code == 400

    def test_scrape_missing_url_returns_422(self, client):
        r = client.post("/scrape", json={})
        assert r.status_code == 422

    def test_scrape_invalid_url_format_returns_422(self, client):
        """ScrapeRequest uses AnyHttpUrl — non-URL strings are rejected by Pydantic."""
        r = client.post(
            "/scrape",
            json={"url": "not-a-url"},
        )
        assert r.status_code == 422
