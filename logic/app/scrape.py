import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import os
from pathlib import Path
from dotenv import load_dotenv
import json
import re

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class JobScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("Warning: OPENAI_API_KEY not found in .env file. GPT-4 scraping will not work.")

    def scrape_url(self, url: str) -> Dict[str, Optional[str]]:
        """
        Scrape job details from a given URL using GPT-4.
        1. Fetches the HTML content
        2. Extracts clean text from the main content area
        3. Sends to GPT-4 for structured extraction
        """
        try:
            # Fetch the HTML content
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # Parse HTML and extract clean text
            soup = BeautifulSoup(response.content, 'html.parser')
            clean_text = self._extract_clean_text(soup)

            # Use GPT-4 to extract structured data
            job_data = self._extract_with_gpt4(clean_text, url)

            # Add the clean text content to the result
            job_data['clean_text_content'] = clean_text

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
            {'class': re.compile(r'job[-_]?description', re.I)},
            {'class': re.compile(r'job[-_]?detail', re.I)},
            {'class': re.compile(r'job[-_]?content', re.I)},
            {'id': re.compile(r'job[-_]?description', re.I)},
            {'id': re.compile(r'job[-_]?detail', re.I)},
            {'role': 'main'},
            {'class': re.compile(r'main[-_]?content', re.I)},
        ]

        for selector in selectors:
            main_content = soup.find(attrs=selector)
            if main_content:
                break

        # If no main content found, use the body
        if not main_content:
            main_content = soup.find('body')

        if not main_content:
            main_content = soup

        # Get text and clean it up
        text = main_content.get_text(separator='\n', strip=True)

        # Remove excessive whitespace and empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)

        # Limit text length to avoid token limits (approximately 10k tokens = 40k chars)
        if len(clean_text) > 40000:
            clean_text = clean_text[:40000] + "\n...(content truncated)"

        return clean_text

    def _extract_with_gpt4(self, text: str, url: str) -> Dict[str, Optional[str]]:
        """
        Use GPT-4 to extract structured job information from clean text.
        """
        if not self.openai_api_key:
            raise Exception("OPENAI_API_KEY not configured. Please add it to your .env file.")

        # Construct the prompt for GPT-4
        prompt = f"""Extract job posting information from the following text and return it as JSON.

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
            # Call OpenAI API
            api_url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts structured job information from text. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }

            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            gpt_response = result['choices'][0]['message']['content'].strip()

            # Clean up the response (remove markdown code blocks if present)
            gpt_response = re.sub(r'^```json\s*', '', gpt_response)
            gpt_response = re.sub(r'^```\s*', '', gpt_response)
            gpt_response = re.sub(r'\s*```$', '', gpt_response)

            # Parse JSON response
            job_data = json.loads(gpt_response)

            # Add the job URL
            job_data['job_url'] = url

            return job_data

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse GPT-4 response as JSON: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"GPT-4 extraction failed: {str(e)}")
