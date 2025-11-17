
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from typing import Dict, Optional

class JobScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_url(self, url: str) -> Dict[str, Optional[str]]:
        """
        Scrape job details from a given URL.
        Attempts to identify the site and use appropriate scraping logic.
        """
        try:
            domain = urlparse(url).netloc.lower()
            
            # Route to appropriate scraper based on domain
            if 'gradcracker' in domain:
                return self._scrape_gradcracker(url)
            elif 'linkedin' in domain:
                return self._scrape_linkedin(url)
            elif 'indeed' in domain:
                return self._scrape_indeed(url)
            elif 'reed' in domain:
                return self._scrape_reed(url)
            else:
                # Generic scraper for unknown sites
                return self._scrape_generic(url)
                
        except Exception as e:
            raise Exception(f"Failed to scrape URL: {str(e)}")
    
    def _scrape_gradcracker(self, url: str) -> Dict[str, Optional[str]]:
        """Scrape GradCracker job postings"""
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        data = {
            'company_name': None,
            'position_title': None,
            'location': None,
            'salary': None,
            'description': None,
            'requirements': None,
            'job_url': url
        }
        
        # Extract company name
        company_elem = soup.find('div', class_='company-name') or soup.find('a', class_='employer-name')
        if company_elem:
            data['company_name'] = company_elem.get_text(strip=True)
        
        # Extract position title
        title_elem = soup.find('h1', class_='job-title') or soup.find('h1')
        if title_elem:
            data['position_title'] = title_elem.get_text(strip=True)
        
        # Extract location
        location_elem = soup.find('span', class_='location') or soup.find('div', class_='job-location')
        if location_elem:
            data['location'] = location_elem.get_text(strip=True)
        
        # Extract salary
        salary_elem = soup.find('span', class_='salary') or soup.find('div', class_='job-salary')
        if salary_elem:
            data['salary'] = salary_elem.get_text(strip=True)
        
        # Extract description
        desc_elem = soup.find('div', class_='job-description') or soup.find('div', id='job-description')
        if desc_elem:
            data['description'] = desc_elem.get_text(strip=True)
        
        # Extract requirements
        req_elem = soup.find('div', class_='requirements') or soup.find('div', class_='job-requirements')
        if req_elem:
            data['requirements'] = req_elem.get_text(strip=True)
        
        return data
    
    def _scrape_linkedin(self, url: str) -> Dict[str, Optional[str]]:
        """Scrape LinkedIn job postings"""
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        data = {
            'company_name': None,
            'position_title': None,
            'location': None,
            'salary': None,
            'description': None,
            'requirements': None,
            'job_url': url
        }
        
        # LinkedIn structure (may require login for full access)
        title_elem = soup.find('h1', class_='top-card-layout__title')
        if title_elem:
            data['position_title'] = title_elem.get_text(strip=True)
        
        company_elem = soup.find('a', class_='topcard__org-name-link')
        if company_elem:
            data['company_name'] = company_elem.get_text(strip=True)
        
        location_elem = soup.find('span', class_='topcard__flavor--bullet')
        if location_elem:
            data['location'] = location_elem.get_text(strip=True)
        
        desc_elem = soup.find('div', class_='show-more-less-html__markup')
        if desc_elem:
            data['description'] = desc_elem.get_text(strip=True)
        
        return data
    
    def _scrape_indeed(self, url: str) -> Dict[str, Optional[str]]:
        """Scrape Indeed job postings"""
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        data = {
            'company_name': None,
            'position_title': None,
            'location': None,
            'salary': None,
            'description': None,
            'requirements': None,
            'job_url': url
        }
        
        # Extract title
        title_elem = soup.find('h1', class_='jobsearch-JobInfoHeader-title')
        if title_elem:
            data['position_title'] = title_elem.get_text(strip=True)
        
        # Extract company
        company_elem = soup.find('div', {'data-company-name': True})
        if company_elem:
            data['company_name'] = company_elem.get('data-company-name')
        else:
            company_elem = soup.find('span', class_='css-1saizt3')
            if company_elem:
                data['company_name'] = company_elem.get_text(strip=True)
        
        # Extract location
        location_elem = soup.find('div', {'data-testid': 'job-location'})
        if location_elem:
            data['location'] = location_elem.get_text(strip=True)
        
        # Extract salary
        salary_elem = soup.find('div', id='salaryInfoAndJobType')
        if salary_elem:
            data['salary'] = salary_elem.get_text(strip=True)
        
        # Extract description
        desc_elem = soup.find('div', id='jobDescriptionText')
        if desc_elem:
            data['description'] = desc_elem.get_text(strip=True)
        
        return data
    
    def _scrape_reed(self, url: str) -> Dict[str, Optional[str]]:
        """Scrape Reed.co.uk job postings"""
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        data = {
            'company_name': None,
            'position_title': None,
            'location': None,
            'salary': None,
            'description': None,
            'requirements': None,
            'job_url': url
        }
        
        # Extract title
        title_elem = soup.find('h1')
        if title_elem:
            data['position_title'] = title_elem.get_text(strip=True)
        
        # Extract company
        company_elem = soup.find('span', {'itemprop': 'hiringOrganization'})
        if company_elem:
            data['company_name'] = company_elem.get_text(strip=True)
        
        # Extract location
        location_elem = soup.find('span', {'itemprop': 'jobLocation'})
        if location_elem:
            data['location'] = location_elem.get_text(strip=True)
        
        # Extract salary
        salary_elem = soup.find('span', {'data-qa': 'salaryLbl'})
        if salary_elem:
            data['salary'] = salary_elem.get_text(strip=True)
        
        # Extract description
        desc_elem = soup.find('span', {'itemprop': 'description'})
        if desc_elem:
            data['description'] = desc_elem.get_text(strip=True)
        
        return data
    
    def _scrape_generic(self, url: str) -> Dict[str, Optional[str]]:
        """
        Generic scraper that attempts to extract job info from any site
        using common patterns and heuristics
        """
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        data = {
            'company_name': None,
            'position_title': None,
            'location': None,
            'salary': None,
            'description': None,
            'requirements': None,
            'job_url': url
        }
        
        # Try to find title (usually in h1, or has 'title' in class/id)
        title_elem = soup.find('h1')
        if not title_elem:
            title_elem = soup.find(class_=re.compile('title|job-title|position', re.I))
        if title_elem:
            data['position_title'] = title_elem.get_text(strip=True)
        
        # Try to find company (look for 'company' in class/id)
        company_elem = soup.find(class_=re.compile('company|employer|organization', re.I))
        if company_elem:
            data['company_name'] = company_elem.get_text(strip=True)
        
        # Try to find location (look for 'location' in class/id)
        location_elem = soup.find(class_=re.compile('location|address|place', re.I))
        if location_elem:
            data['location'] = location_elem.get_text(strip=True)
        
        # Try to find salary (look for 'salary' or currency symbols)
        salary_elem = soup.find(class_=re.compile('salary|wage|pay|compensation', re.I))
        if salary_elem:
            data['salary'] = salary_elem.get_text(strip=True)
        
        # Try to find description (usually longest text block)
        desc_elem = soup.find(class_=re.compile('description|details|content', re.I))
        if desc_elem:
            data['description'] = desc_elem.get_text(strip=True)
        
        return data


# Alternative: Selenium-based scraper for JavaScript-heavy sites
# Uncomment this if you need to scrape sites that require JavaScript

"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class SeleniumJobScraper:
    def __init__(self):
        self.options = Options()
        self.options.add_argument('--headless')  # Run in background
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    def scrape_url(self, url: str) -> Dict[str, Optional[str]]:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )
        
        try:
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            data = {
                'company_name': None,
                'position_title': None,
                'location': None,
                'salary': None,
                'description': None,
                'requirements': None,
                'job_url': url
            }
            
            # Extract title
            try:
                title_elem = driver.find_element(By.TAG_NAME, "h1")
                data['position_title'] = title_elem.text
            except:
                pass
            
            # Extract company (modify selectors based on target site)
            try:
                company_elem = driver.find_element(By.CSS_SELECTOR, "[class*='company']")
                data['company_name'] = company_elem.text
            except:
                pass
            
            # Extract location
            try:
                location_elem = driver.find_element(By.CSS_SELECTOR, "[class*='location']")
                data['location'] = location_elem.text
            except:
                pass
            
            # Extract description
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, "[class*='description']")
                data['description'] = desc_elem.text
            except:
                pass
            
            return data
            
        finally:
            driver.quit()
"""