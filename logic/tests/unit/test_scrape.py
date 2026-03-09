"""
Unit tests for app/scrape.py

Covers:
- SSRF protection (_validate_url_for_ssrf) — security-critical
- HTML text extraction (_extract_clean_text)
- 24-hour caching behaviour in scrape_url
"""
import json
import hashlib
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bs4 import BeautifulSoup
from pathlib import Path

from app.scrape import _validate_url_for_ssrf, JobScraper


# ---------------------------------------------------------------------------
# SSRF Protection (security-critical — every case must stay green)
# ---------------------------------------------------------------------------

class TestValidateUrlForSsrf:
    """_validate_url_for_ssrf must raise ValueError for any non-public address."""

    # --- Should PASS (no exception) ---

    def test_allows_public_https_url(self):
        with patch("app.scrape.socket.gethostbyname", return_value="104.18.7.53"):
            _validate_url_for_ssrf("https://jobs.lever.co/stripe/abc123")

    def test_allows_public_http_url(self):
        with patch("app.scrape.socket.gethostbyname", return_value="93.184.216.34"):
            _validate_url_for_ssrf("http://www.example.com/careers/job-1")

    # --- Should BLOCK ---

    def test_blocks_localhost_127_0_0_1(self):
        with patch("app.scrape.socket.gethostbyname", return_value="127.0.0.1"):
            with pytest.raises(ValueError, match="private or reserved"):
                _validate_url_for_ssrf("http://localhost/admin")

    def test_blocks_loopback_127_1_2_3(self):
        with patch("app.scrape.socket.gethostbyname", return_value="127.1.2.3"):
            with pytest.raises(ValueError, match="private or reserved"):
                _validate_url_for_ssrf("http://127.1.2.3/secret")

    def test_blocks_10_dot_network(self):
        with patch("app.scrape.socket.gethostbyname", return_value="10.0.0.1"):
            with pytest.raises(ValueError, match="private or reserved"):
                _validate_url_for_ssrf("http://10.0.0.1/internal-api")

    def test_blocks_172_16_range(self):
        with patch("app.scrape.socket.gethostbyname", return_value="172.16.5.100"):
            with pytest.raises(ValueError, match="private or reserved"):
                _validate_url_for_ssrf("http://internal.corp.local/")

    def test_blocks_192_168_network(self):
        with patch("app.scrape.socket.gethostbyname", return_value="192.168.1.1"):
            with pytest.raises(ValueError, match="private or reserved"):
                _validate_url_for_ssrf("http://192.168.1.1/router")

    def test_blocks_cloud_metadata_endpoint(self):
        """169.254.169.254 is the AWS/GCP/Azure instance metadata endpoint."""
        with patch("app.scrape.socket.gethostbyname", return_value="169.254.169.254"):
            with pytest.raises(ValueError, match="private or reserved"):
                _validate_url_for_ssrf("http://169.254.169.254/latest/meta-data/")

    def test_blocks_javascript_scheme(self):
        with pytest.raises(ValueError, match="not allowed"):
            _validate_url_for_ssrf("javascript:alert(document.cookie)")

    def test_blocks_file_scheme(self):
        with pytest.raises(ValueError, match="not allowed"):
            _validate_url_for_ssrf("file:///etc/passwd")

    def test_blocks_ftp_scheme(self):
        with pytest.raises(ValueError, match="not allowed"):
            _validate_url_for_ssrf("ftp://files.internal.corp/confidential")

    def test_blocks_url_with_no_hostname(self):
        with pytest.raises(ValueError, match="no hostname"):
            _validate_url_for_ssrf("http:///path-only")

    def test_blocks_unresolvable_hostname(self):
        import socket
        with patch("app.scrape.socket.gethostbyname", side_effect=socket.gaierror("resolution failed")):
            with pytest.raises(ValueError, match="could not be resolved"):
                _validate_url_for_ssrf("http://does-not-exist.fake/jobs/1")


# ---------------------------------------------------------------------------
# HTML Text Extraction
# ---------------------------------------------------------------------------

class TestExtractCleanText:
    """_extract_clean_text should return clean job content from HTML."""

    @pytest.fixture()
    def scraper(self):
        return JobScraper()

    def _soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    def test_removes_script_tags(self, scraper):
        soup = self._soup("""
        <html><body>
          <script>var tracking = "evil";</script>
          <main>Actual job content here</main>
        </body></html>
        """)
        result = scraper._extract_clean_text(soup)
        assert 'var tracking' not in result
        assert 'Actual job content here' in result

    def test_removes_style_tags(self, scraper):
        soup = self._soup("""
        <html><body>
          <style>.class { color: red; font-size: 12px; }</style>
          <p>Job description content</p>
        </body></html>
        """)
        result = scraper._extract_clean_text(soup)
        assert 'color: red' not in result
        assert 'Job description content' in result

    def test_removes_nav_and_footer_noise(self, scraper):
        soup = self._soup("""
        <html><body>
          <nav>Company | Careers | Login | Sign Up</nav>
          <div class="job-description">Senior Python Engineer role</div>
          <footer>Copyright 2024 Corp Inc</footer>
        </body></html>
        """)
        result = scraper._extract_clean_text(soup)
        assert 'Company | Careers' not in result
        assert 'Copyright 2024' not in result
        assert 'Senior Python Engineer role' in result

    def test_prefers_job_description_class(self, scraper):
        soup = self._soup("""
        <html><body>
          <div class="sidebar">Unrelated sidebar content</div>
          <div class="job-description">We are hiring a SWE</div>
        </body></html>
        """)
        result = scraper._extract_clean_text(soup)
        assert 'We are hiring a SWE' in result
        # Sidebar should be excluded when job-description div is present
        assert 'Unrelated sidebar content' not in result

    def test_falls_back_to_body_when_no_job_selector_found(self, scraper):
        soup = self._soup("""
        <html><body>
          <p>Generic page with job posting somewhere in the body</p>
        </body></html>
        """)
        result = scraper._extract_clean_text(soup)
        assert 'Generic page with job posting' in result

    def test_truncates_content_at_40000_chars(self, scraper):
        big_text = "x" * 50_000
        soup = self._soup(f"<html><body><p>{big_text}</p></body></html>")
        result = scraper._extract_clean_text(soup)
        assert len(result) <= 40_100  # 40000 + "...(content truncated)"
        assert "truncated" in result

    def test_does_not_truncate_content_under_40000_chars(self, scraper):
        short_text = "Python Engineer needed " * 100  # ~2200 chars
        soup = self._soup(f"<html><body><p>{short_text}</p></body></html>")
        result = scraper._extract_clean_text(soup)
        assert "truncated" not in result


# ---------------------------------------------------------------------------
# Caching Logic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scrape_url_returns_cached_result_without_fetching(tmp_path):
    """If a fresh cache file exists, scrape_url must return it without any HTTP/AI calls."""
    scraper = JobScraper()
    scraper.cache_dir = tmp_path  # redirect to temp dir

    url = "https://jobs.example.com/engineer/123"
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    cache_file = tmp_path / f"{url_hash}.json"

    cached = {
        "company_name": "Cached Corp",
        "position_title": "Cached Engineer",
        "job_url": url,
        "clean_text_content": "cached text",
    }
    cache_file.write_text(json.dumps(cached))

    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock) as mock_fetch, \
         patch.object(scraper, "_extract_with_gemini", new_callable=AsyncMock) as mock_gemini, \
         patch("app.scrape.socket.gethostbyname", return_value="93.184.216.34"):
        result = await scraper.scrape_url(url, "fake-api-key")

    mock_fetch.assert_not_called()
    mock_gemini.assert_not_called()
    assert result["company_name"] == "Cached Corp"
    assert result["position_title"] == "Cached Engineer"


@pytest.mark.asyncio
async def test_scrape_url_fetches_when_cache_is_stale(tmp_path):
    """A cache file older than 24 hours must not be used."""
    import os
    import time

    scraper = JobScraper()
    scraper.cache_dir = tmp_path

    url = "https://jobs.example.com/stale/456"
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    cache_file = tmp_path / f"{url_hash}.json"

    stale = {"company_name": "Stale Corp", "position_title": "Stale Role", "job_url": url}
    cache_file.write_text(json.dumps(stale))

    # Set the modification time to 25 hours ago
    old_time = time.time() - 90_000  # 25 hours
    os.utime(cache_file, (old_time, old_time))

    fresh_result = {
        "company_name": "Fresh Corp",
        "position_title": "Fresh Role",
        "job_url": url,
    }

    with patch.object(scraper, "_fetch_html", new_callable=AsyncMock, return_value="<html>fresh</html>"), \
         patch.object(scraper, "_extract_with_gemini", new_callable=AsyncMock, return_value=fresh_result), \
         patch("app.scrape.socket.gethostbyname", return_value="93.184.216.34"):
        # Mock BeautifulSoup so _extract_clean_text doesn't crash on minimal HTML
        with patch("app.scrape.BeautifulSoup") as mock_bs:
            mock_soup = MagicMock()
            mock_bs.return_value = mock_soup
            scraper._extract_clean_text = MagicMock(return_value="fresh text")
            result = await scraper.scrape_url(url, "fake-api-key")

    assert result["company_name"] == "Fresh Corp"


@pytest.mark.asyncio
async def test_scrape_url_raises_on_ssrf_url(tmp_path):
    """SSRF guard must fire before any network call is made."""
    scraper = JobScraper()
    scraper.cache_dir = tmp_path

    with patch("app.scrape.socket.gethostbyname", return_value="192.168.1.1"):
        with pytest.raises(Exception, match="private or reserved"):
            await scraper.scrape_url("http://192.168.1.1/internal", "fake-key")
