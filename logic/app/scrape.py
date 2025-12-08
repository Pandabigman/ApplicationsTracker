from bs4 import BeautifulSoup
from typing import Dict, Optional
import os
from pathlib import Path
from dotenv import load_dotenv
import json
from playwright.async_api import async_playwright
import google.generativeai as genai
import re
import asyncio
import hashlib
from datetime import datetime, timedelta

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.cache_dir = Path(__file__).parent.parent / "cache" / "scrape_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(hours=24)  # Cache scrapes for 24 hours

        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
        else:
            print(
                "Warning: GOOGLE_API_KEY not found in .env file. Gemini scraping will not work."
            )

    async def scrape_url(self, url: str) -> Dict[str, Optional[str]]:
        """
        Scrape job details from a given URL using an AI model.
        1. Fetches the HTML content
        2. Extracts clean text from the main content area
        3. Sends to OpenAI for structured extraction
        """
        try:
            # --- Caching Logic ---
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            cache_file = self.cache_dir / f"{url_hash}.json"

            # Check for a valid cache file
            if cache_file.exists():
                file_mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - file_mod_time < self.cache_duration:
                    print(f"Cache hit for URL: {url}")
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return json.load(f)

            print(f"Cache miss for URL: {url}")

            # Fetch the HTML content using Playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(user_agent=self.headers["User-Agent"])
                await page.goto(url, timeout=20000, wait_until="domcontentloaded")
                content = await page.content()
                await browser.close()

            # Parse HTML and extract clean text
            soup = BeautifulSoup(content, "html.parser")
            clean_text = self._extract_clean_text(soup)

            # Use OpenAI to extract structured data
            job_data = await self._extract_with_gemini(clean_text, url)

            # Add the clean text content to the result
            job_data["clean_text_content"] = clean_text

            # Save result to cache
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(job_data, f, ensure_ascii=False, indent=4)

            return job_data

        except Exception as e:
            raise Exception(f"Failed to scrape URL: {str(e)}")

    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """
        Extract clean text content from HTML, removing navigation, ads, etc.
        """
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Try to find the main content area
        # Look for common job posting containers
        main_content = None

        # Try common job posting selectors
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

        # If no main content found, use the body
        if not main_content:
            main_content = soup.find("body")

        if not main_content:
            main_content = soup

        # Get text and clean it up
        text = main_content.get_text(separator="\n", strip=True)

        # Remove excessive whitespace and empty lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean_text = "\n".join(lines)

        # Limit text length to avoid token limits (approximately 10k tokens = 40k chars)
        if len(clean_text) > 40000:
            clean_text = clean_text[:40000] + "\n...(content truncated)"
            print("content was too long and truncated")

        return clean_text

    async def _extract_with_gemini(
        self, text: str, url: str
    ) -> Dict[str, Optional[str]]:
        """
        Use Google Gemini to extract structured job information from clean text.
        """
        if not self.google_api_key:
            raise Exception(
                "GOOGLE_API_KEY not configured. Please add it to your .env file."
            )

        # Construct the prompt for Gemini
        prompt = f"""Extract job posting information from the following text and return it as a single, valid JSON object.

The text is from this URL: {url}

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

            # --- Retry Logic for API Rate Limiting ---
            max_retries = 3
            delay = 5  # Initial delay in seconds

            for attempt in range(max_retries):
                try:
                    # The google-generativeai library has its own retry mechanism for some errors,
                    # but we add our own for explicit control over 429s.
                    response = await model.generate_content_async(prompt)
                    break  # Success, exit loop
                except genai.types.generation_types.BlockedPromptException as e:
                    # If the prompt is blocked for safety reasons, we can't retry.
                    raise Exception(f"Gemini prompt was blocked: {e}")
                except Exception as e:
                    # Catching potential rate limit errors (often appear as 503 or 429)
                    # The Gemini library may abstract this, so we check the error message.
                    is_rate_limit = (
                        "429" in str(e)
                        or "resource has been exhausted" in str(e).lower()
                    )
                    if is_rate_limit and attempt < max_retries - 1:
                        print(
                            f"Rate limit hit. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        raise  # Re-raise the exception if it's not a rate limit or if it's the last attempt

            # --- End Retry Logic ---
            gemini_response = response.text.strip()

            # Clean up the response (remove markdown code blocks if present)
            gemini_response = re.sub(r"^```json\s*", "", gemini_response)
            gemini_response = re.sub(r"^```\s*", "", gemini_response)
            gemini_response = re.sub(r"\s*```$", "", gemini_response)

            # Parse JSON response
            job_data = json.loads(gemini_response)

            # Add the job URL
            job_data["job_url"] = url

            return job_data

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Gemini extraction failed: {str(e)}")
