from bs4 import BeautifulSoup
from typing import Dict, Optional
import os
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
import json
import httpx
import google.generativeai as genai
import re
import asyncio
import hashlib
from datetime import datetime, timedelta

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


_PRIVATE_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / cloud metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _validate_url_for_ssrf(url: str) -> None:
    """Raise ValueError if the URL targets a private/loopback/metadata address."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme '{parsed.scheme}' is not allowed.")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname.")
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
    except socket.gaierror:
        raise ValueError("URL hostname could not be resolved.")
    for net in _PRIVATE_NETS:
        if ip in net:
            raise ValueError("URL targets a private or reserved address.")


class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.cache_dir = Path(__file__).parent.parent / "cache" / "scrape_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(hours=24)

    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML content using ScrapingBee for JS-rendered pages."""
        scrapingbee_key = os.environ.get("SCRAPINGBEE_API_KEY")

        if scrapingbee_key:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://app.scrapingbee.com/api/v1/",
                    params={
                        "api_key": scrapingbee_key,
                        "url": url,
                        "render_js": "true",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.text
        else:
            # Fallback: plain HTTP fetch (no JS rendering)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    follow_redirects=True,
                    timeout=20.0,
                )
                response.raise_for_status()
                return response.text

    async def scrape_url(self, url: str, gemini_api_key: str) -> Dict[str, Optional[str]]:
        """
        Scrape job details from a given URL using an AI model.
        1. Fetches the HTML content via ScrapingBee
        2. Extracts clean text from the main content area
        3. Sends to Gemini for structured extraction
        """
        try:
            # SSRF guard — must run before any network access
            _validate_url_for_ssrf(url)

            # --- Caching Logic ---
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            cache_file = self.cache_dir / f"{url_hash}.json"

            if cache_file.exists():
                file_mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - file_mod_time < self.cache_duration:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return json.load(f)

            # Fetch the HTML content
            content = await self._fetch_html(url)

            # Parse HTML and extract clean text
            soup = BeautifulSoup(content, "html.parser")
            clean_text = self._extract_clean_text(soup)

            # Use Gemini to extract structured data
            job_data = await self._extract_with_gemini(clean_text, url, gemini_api_key)

            # Add the clean text content to the result
            job_data["clean_text_content"] = clean_text

            # Save result to cache
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(job_data, f, ensure_ascii=False, indent=4)

            return job_data

        except Exception as e:
            raise Exception(f"Failed to scrape URL: {str(e)}")

    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML, removing navigation, ads, etc."""
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        main_content = None
        selectors = [
            {"class": re.compile(r"job[-_]?description", re.I)},
            {"class": re.compile(r"job[-_]?detail", re.I)},
            {"class": re.compile(r"job[-_]?content", re.I)},
            {"id": re.compile(r"job[-_]?description", re.I)},
            {"id": re.compile(r"job[-_]?detail", re.I)},
            {"role": "main"},
            {"class": re.compile(r"main[-_]?content", re.I)},
        ]

        for selector in selectors:
            main_content = soup.find(attrs=selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.find("body")
        if not main_content:
            main_content = soup

        text = main_content.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean_text = "\n".join(lines)

        if len(clean_text) > 40000:
            clean_text = clean_text[:40000] + "\n...(content truncated)"

        return clean_text

    async def _extract_with_gemini(
        self, text: str, url: str, api_key: str
    ) -> Dict[str, Optional[str]]:
        """Use Google Gemini to extract structured job information from clean text."""
        genai.configure(api_key=api_key)

        prompt = f"""Extract job posting information from the following text and return it as a single, valid JSON object.

Please extract:
- company_name: The company/organization name
- position_title: The job title or position name
- location: Work location (city, country, or "Remote")
- salary: Salary information if mentioned (include currency and range)
- description: A brief summary of the job (2-3 sentences)
- requirements: Key requirements and qualifications (bullet points or short paragraph)
- application_deadline: If mentioned, the deadline to apply (format: YYYY-MM-DD or text description)
- ai_thoughts: Your strategic advice for the candidate. In 3-4 sentences, explain:
  * What makes a strong candidate stand out for this role
  * Key skills or experiences to emphasize
  * How to tailor the application/CV for maximum impact
  * Any red flags or challenges to be aware of

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "company_name": "string or null",
  "position_title": "string or null",
  "location": "string or null",
  "salary": "string or null",
  "description": "string or null",
  "requirements": "string or null",
  "application_deadline": "string or null",
  "ai_thoughts": "string with strategic advice"
}}

If any field cannot be determined from the text, use null. Always provide ai_thoughts based on the job description.

TEXT TO ANALYZE:
{text}
"""

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")

            max_retries = 3
            delay = 5

            for attempt in range(max_retries):
                try:
                    response = await model.generate_content_async(prompt)
                    break
                except Exception as e:
                    if hasattr(genai, 'types') and hasattr(genai.types, 'generation_types'):
                        if isinstance(e, genai.types.generation_types.BlockedPromptException):
                            raise Exception(f"Gemini prompt was blocked: {e}")
                    is_rate_limit = (
                        "429" in str(e)
                        or "resource has been exhausted" in str(e).lower()
                    )
                    if is_rate_limit and attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        raise

            gemini_response = response.text.strip()
            gemini_response = re.sub(r"^```json\s*", "", gemini_response)
            gemini_response = re.sub(r"^```\s*", "", gemini_response)
            gemini_response = re.sub(r"\s*```$", "", gemini_response)

            job_data = json.loads(gemini_response)
            job_data["job_url"] = url

            return job_data

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Gemini extraction failed: {str(e)}")
