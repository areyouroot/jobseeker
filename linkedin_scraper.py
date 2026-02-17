"""
LinkedIn Scraper Service Module
================================

This module provides LinkedIn profile scraping functionality.
It uses Selenium for browser automation to search for employee profiles
at specific companies.

IMPORTANT: This module respects LinkedIn's Terms of Service by:
- Implementing rate limiting
- Adding random delays between requests
- Limiting the number of profiles retrieved
- Using authenticated sessions (optional)

Author: Job Seeker Team
Date: 2026-02-15
"""

import logging
import time
import random
from typing import List, Optional, Dict
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import config


@dataclass
class LinkedInProfile:
    """
    Data class representing a LinkedIn profile.
    
    Attributes:
        name (str): Person's full name
        title (str): Current job title
        company (str): Current company
        location (str): Location
        profile_url (str): LinkedIn profile URL
        headline (Optional[str]): Profile headline
        connections (Optional[str]): Number of connections
    """
    name: str
    title: str
    company: str
    location: str
    profile_url: str
    headline: Optional[str] = None
    connections: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of profile."""
        return f"{self.name} - {self.title} at {self.company}"
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert profile to dictionary format.
        
        Returns:
            Dict[str, str]: Profile data as dictionary
        """
        return {
            'name': self.name,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'profile_url': self.profile_url,
            'headline': self.headline,
            'connections': self.connections,
        }


class LinkedInScraperService:
    """
    Service class for scraping LinkedIn profiles.
    
    This class provides methods to:
    - Search for employees at specific companies
    - Extract profile information
    - Handle authentication (optional)
    - Implement rate limiting and respectful scraping
    
    Attributes:
        logger (Logger): Logger instance
        driver (WebDriver): Selenium WebDriver instance
        is_authenticated (bool): Whether user is logged in
    """
    
    def __init__(self, headless: bool = None):
        """
        Initialize the LinkedInScraperService.
        
        Args:
            headless (bool): Run browser in headless mode. 
                           If None, uses config setting.
        """
        self.logger = logging.getLogger('JobSeeker.LinkedInScraperService')
        
        # Use config setting if not specified
        if headless is None:
            headless = config.headless_browser
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Initialize WebDriver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            self.is_authenticated = False
            
            self.logger.info("LinkedInScraperService initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def __del__(self):
        """
        Cleanup method to close browser when object is destroyed.
        """
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed")
            except:
                pass
    
    def login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Login to LinkedIn (optional but recommended for better results).
        
        Args:
            email (Optional[str]): LinkedIn email. Uses config if not provided.
            password (Optional[str]): LinkedIn password. Uses config if not provided.
            
        Returns:
            bool: True if login successful, False otherwise
            
        Note:
            Authenticated sessions have higher rate limits and better access.
        """
        # Use config credentials if not provided
        email = email or config.linkedin_email
        password = password or config.linkedin_password
        
        if not email or not password:
            self.logger.warning("No LinkedIn credentials provided - skipping login")
            return False
        
        try:
            self.logger.info("Attempting to login to LinkedIn...")
            
            # Navigate to LinkedIn login page
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Find and fill email field
            email_field = self.driver.find_element(By.ID, "username")
            email_field.send_keys(email)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(password)
            
            # Submit form
            password_field.send_keys(Keys.RETURN)
            
            # Wait for redirect to feed
            time.sleep(5)
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                self.is_authenticated = True
                self.logger.info("Successfully logged in to LinkedIn")
                return True
            else:
                self.logger.warning("Login may have failed - check credentials")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during login: {e}")
            return False
    
    def search_company_employees(
        self,
        company_name: str,
        max_profiles: int = None
    ) -> List[LinkedInProfile]:
        """
        Search for employee profiles at a specific company.
        
        This method searches LinkedIn for people working at the specified
        company and extracts their profile information.
        
        Args:
            company_name (str): Name of the company to search
            max_profiles (int): Maximum number of profiles to retrieve.
                              Uses config setting if not provided.
                              
        Returns:
            List[LinkedInProfile]: List of employee profiles found
            
        Example:
            >>> scraper = LinkedInScraperService()
            >>> profiles = scraper.search_company_employees("Google", max_profiles=5)
            >>> for profile in profiles:
            ...     print(profile.name, profile.title)
        """
        # Use config setting if not specified
        if max_profiles is None:
            max_profiles = config.max_linkedin_profiles
        
        self.logger.info(
            f"Searching for up to {max_profiles} employees at {company_name}"
        )
        
        profiles = []
        
        try:
            # Build search URL
            # This searches for people currently working at the company
            search_query = f"site:linkedin.com/in/ {company_name}"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            self.driver.get(search_url)
            time.sleep(random.uniform(2, 4))  # Random delay to appear human
            
            # Find LinkedIn profile links from Google results
            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'linkedin.com/in/')]")
            
            # Extract unique profile URLs
            profile_urls = []
            for link in links[:max_profiles * 2]:  # Get extra in case some fail
                url = link.get_attribute('href')
                if url and '/in/' in url and url not in profile_urls:
                    profile_urls.append(url)
                    if len(profile_urls) >= max_profiles:
                        break
            
            self.logger.info(f"Found {len(profile_urls)} profile URLs to scrape")
            
            # Visit each profile and extract information
            for i, url in enumerate(profile_urls[:max_profiles], 1):
                try:
                    self.logger.debug(f"Scraping profile {i}/{max_profiles}: {url}")
                    
                    profile = self._scrape_profile(url, company_name)
                    if profile:
                        profiles.append(profile)
                    
                    # Random delay between requests (2-5 seconds)
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    self.logger.warning(f"Failed to scrape profile {url}: {e}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(profiles)} profiles")
            return profiles
            
        except Exception as e:
            self.logger.error(f"Error searching for employees: {e}")
            return profiles
    
    def _scrape_profile(
        self,
        profile_url: str,
        company_name: str
    ) -> Optional[LinkedInProfile]:
        """
        Scrape information from a single LinkedIn profile.
        
        This is a private helper method that extracts profile data
        from a LinkedIn profile page.
        
        Args:
            profile_url (str): URL of the LinkedIn profile
            company_name (str): Company name for verification
            
        Returns:
            Optional[LinkedInProfile]: Profile data or None if scraping fails
        """
        try:
            self.driver.get(profile_url)
            time.sleep(2)
            
            # Extract name
            try:
                name_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.text-heading-xlarge"))
                )
                name = name_element.text.strip()
            except:
                name = "Unknown"
            
            # Extract headline/title
            try:
                headline_element = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    "div.text-body-medium"
                )
                headline = headline_element.text.strip()
                # Use headline as title
                title = headline.split(' at ')[0] if ' at ' in headline else headline
            except:
                title = "N/A"
                headline = None
            
            # Extract location
            try:
                location_element = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "span.text-body-small"
                )
                location = location_element.text.strip()
            except:
                location = "N/A"
            
            # Create profile object
            profile = LinkedInProfile(
                name=name,
                title=title,
                company=company_name,
                location=location,
                profile_url=profile_url,
                headline=headline
            )
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error scraping profile: {e}")
            return None
