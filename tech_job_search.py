"""
Specialized IT/Tech Company Job Search Script
==============================================

This script searches for IT and tech companies that might hire for:
- Cyber Security positions
- Full Stack Development positions
- Other tech roles

It extracts comprehensive information including:
- Company name and address
- LinkedIn company profile
- LinkedIn employee profiles (up to 5)
- Job openings (if available)
- Email addresses
- Company type/category

Author: Job Seeker Team
Date: 2026-02-15
"""

import logging
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from location_service import LocationService, Location
from company_search import CompanySearchService, Company
from linkedin_scraper import LinkedInScraperService, LinkedInProfile
from config import config

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@dataclass
class TechCompanyDetails:
    """
    Extended company details for tech companies.
    
    Attributes:
        company (Company): Base company information
        company_linkedin_url (Optional[str]): LinkedIn company page URL
        employee_profiles (List[LinkedInProfile]): Employee LinkedIn profiles
        job_openings (List[str]): Available job postings
        emails (List[str]): Contact email addresses
        company_type (str): Type of tech company
        tech_stack (List[str]): Technologies used (if available)
    """
    company: Company
    company_linkedin_url: Optional[str] = None
    employee_profiles: List[LinkedInProfile] = field(default_factory=list)
    job_openings: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    company_type: str = "Technology"
    tech_stack: List[str] = field(default_factory=list)
    
    def to_formatted_text(self) -> str:
        """
        Convert to formatted text for output file.
        
        Returns:
            str: Formatted company information
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"COMPANY: {self.company.name}")
        lines.append("=" * 80)
        lines.append(f"Type: {self.company_type}")
        lines.append(f"Category: {self.company.category}")
        lines.append(f"Distance: {self.company.distance_km:.2f} km")
        lines.append(f"\nAddress: {self.company.address}")
        
        if self.company.phone:
            lines.append(f"Phone: {self.company.phone}")
        
        if self.company.website:
            lines.append(f"Website: {self.company.website}")
        
        if self.company_linkedin_url:
            lines.append(f"\nLinkedIn Company: {self.company_linkedin_url}")
        
        if self.emails:
            lines.append(f"\nEmails:")
            for email in self.emails:
                lines.append(f"  - {email}")
        
        if self.tech_stack:
            lines.append(f"\nTech Stack: {', '.join(self.tech_stack)}")
        
        if self.job_openings:
            lines.append(f"\nJob Openings ({len(self.job_openings)}):")
            for i, job in enumerate(self.job_openings, 1):
                lines.append(f"  {i}. {job}")
        
        if self.employee_profiles:
            lines.append(f"\nEmployee LinkedIn Profiles ({len(self.employee_profiles)}):")
            for i, profile in enumerate(self.employee_profiles, 1):
                lines.append(f"  {i}. {profile.name}")
                lines.append(f"     Title: {profile.title}")
                lines.append(f"     Location: {profile.location}")
                lines.append(f"     Profile: {profile.profile_url}")
                if i < len(self.employee_profiles):
                    lines.append("")
        
        lines.append("\n")
        return "\n".join(lines)


class TechJobSearchService:
    """
    Specialized service for searching tech companies and job opportunities.
    
    This service extends the base functionality to focus on:
    - IT and technology companies
    - Cyber security and full stack development roles
    - Comprehensive information extraction
    """
    
    # Tech-related keywords for filtering
    TECH_KEYWORDS = [
        'software', 'technology', 'tech', 'it', 'computer', 'digital',
        'cyber', 'security', 'development', 'programming', 'coding',
        'web', 'mobile', 'cloud', 'data', 'ai', 'ml', 'analytics'
    ]
    
    # Job role keywords
    JOB_KEYWORDS = [
        'cyber security', 'security analyst', 'security engineer',
        'full stack', 'developer', 'software engineer', 'programmer',
        'web developer', 'backend', 'frontend', 'devops'
    ]
    
    def __init__(self):
        """Initialize the tech job search service."""
        self.logger = logging.getLogger('JobSeeker.TechJobSearch')
        self.location_service = LocationService()
        self.company_service = CompanySearchService()
        self.linkedin_service = None  # Lazy initialization
        
        self.logger.info("TechJobSearchService initialized")
    
    def search_tech_companies(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0
    ) -> List[Company]:
        """
        Search for tech companies near the specified coordinates.
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            radius_km (float): Search radius in kilometers
            
        Returns:
            List[Company]: List of tech companies found
        """
        self.logger.info(f"Searching for tech companies at ({latitude}, {longitude})")
        
        # Create location object
        location = self.location_service.reverse_geocode(latitude, longitude)
        
        if not location:
            self.logger.error("Failed to reverse geocode coordinates")
            return []
        
        # Search all companies
        all_companies = self.company_service.search_companies(location, radius_km)
        
        self.logger.info(f"Total companies found: {len(all_companies)}")
        
        # Filter for tech companies with more inclusive criteria
        tech_companies = []
        for company in all_companies:
            # Check if company name or category contains tech keywords
            company_text = f"{company.name} {company.category}".lower()
            
            # Check for tech keywords
            is_tech = any(keyword in company_text for keyword in self.TECH_KEYWORDS)
            
            # Also include companies in office/industrial categories as they might be tech
            is_office = company.category in ['office', 'industrial', 'commercial', 'business']
            
            if is_tech or is_office:
                tech_companies.append(company)
        
        self.logger.info(f"Found {len(tech_companies)} potential tech companies out of {len(all_companies)} total")
        
        # If still no results, return top companies by distance
        if not tech_companies and all_companies:
            self.logger.warning("No tech-specific companies found, returning all companies for manual filtering")
            tech_companies = all_companies[:100]  # Return top 100 closest
        
        return tech_companies
    
    def find_company_linkedin(self, company_name: str) -> Optional[str]:
        """
        Find LinkedIn company page URL.
        
        Args:
            company_name (str): Company name
            
        Returns:
            Optional[str]: LinkedIn company URL or None
        """
        try:
            # Search Google for LinkedIn company page
            search_query = f"{company_name} linkedin company"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find LinkedIn company URL
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'linkedin.com/company/' in href:
                    # Extract clean URL
                    if 'url?q=' in href:
                        url = href.split('url?q=')[1].split('&')[0]
                    else:
                        url = href
                    return url
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding LinkedIn for {company_name}: {e}")
            return None
    
    def extract_emails_from_website(self, website_url: str) -> List[str]:
        """
        Extract email addresses from company website.
        
        Args:
            website_url (str): Company website URL
            
        Returns:
            List[str]: List of email addresses found
        """
        import re
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(website_url, headers=headers, timeout=10)
            
            # Email regex pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, response.text)
            
            # Remove duplicates and common false positives
            emails = list(set(emails))
            emails = [e for e in emails if not any(x in e.lower() for x in ['example', 'test', 'sample'])]
            
            return emails[:3]  # Return max 3 emails
            
        except Exception as e:
            self.logger.debug(f"Could not extract emails from {website_url}: {e}")
            return []
    
    def get_detailed_company_info(
        self,
        company: Company,
        include_linkedin: bool = True
    ) -> TechCompanyDetails:
        """
        Get detailed information about a tech company.
        
        Args:
            company (Company): Base company information
            include_linkedin (bool): Whether to search LinkedIn
            
        Returns:
            TechCompanyDetails: Comprehensive company details
        """
        self.logger.info(f"Getting detailed info for {company.name}")
        
        details = TechCompanyDetails(company=company)
        
        # Find company LinkedIn
        if include_linkedin:
            details.company_linkedin_url = self.find_company_linkedin(company.name)
            time.sleep(random.uniform(1, 2))  # Rate limiting
        
        # Extract emails from website
        if company.website:
            details.emails = self.extract_emails_from_website(company.website)
            time.sleep(random.uniform(1, 2))
        
        # Get employee profiles from LinkedIn
        if include_linkedin:
            if self.linkedin_service is None:
                self.linkedin_service = LinkedInScraperService()
            
            try:
                profiles = self.linkedin_service.search_company_employees(
                    company.name,
                    max_profiles=5
                )
                details.employee_profiles = profiles
            except Exception as e:
                self.logger.error(f"Error getting LinkedIn profiles: {e}")
        
        return details
    
    def generate_company_list(
        self,
        companies: List[TechCompanyDetails],
        output_file: str = "company_list.txt"
    ) -> None:
        """
        Generate formatted company list file.
        
        Args:
            companies (List[TechCompanyDetails]): List of companies with details
            output_file (str): Output file path
        """
        self.logger.info(f"Generating company list to {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("TECH COMPANIES - JOB SEARCH RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Companies: {len(companies)}\n")
            f.write(f"Focus: Cyber Security & Full Stack Development Opportunities\n")
            f.write("=" * 80 + "\n\n")
            
            # Company details
            for i, company_details in enumerate(companies, 1):
                f.write(f"\n[{i}/{len(companies)}]\n")
                f.write(company_details.to_formatted_text())
        
        self.logger.info(f"Company list generated successfully: {output_file}")


def main():
    """Main execution function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "=" * 80)
    print("SPECIALIZED TECH COMPANY JOB SEARCH")
    print("=" * 80)
    
    # Coordinates: 13°01'10.3"N 80°06'58.6"E
    latitude = 13.0195278  # 13 + 1/60 + 10.3/3600
    longitude = 80.1162778  # 80 + 6/60 + 58.6/3600
    radius_km = 25.0
    
    print(f"\nSearch Location: {latitude}°N, {longitude}°E")
    print(f"Search Radius: {radius_km} km")
    print(f"Focus: IT/Tech companies for Cyber Security & Full Stack Development\n")
    
    # Initialize service
    service = TechJobSearchService()
    
    # Search for tech companies
    print("🔍 Searching for tech companies...")
    tech_companies = service.search_tech_companies(latitude, longitude, radius_km)
    
    if not tech_companies:
        print("❌ No tech companies found in the area.")
        return
    
    print(f"✓ Found {len(tech_companies)} tech companies!")
    
    # Get detailed information
    print(f"\n📊 Extracting detailed information for top companies...")
    print("⏱️  This may take a while due to rate limiting...\n")
    
    # Process top 30 companies for detailed info
    companies_to_process = min(len(tech_companies), 30)
    detailed_companies = []
    
    for i, company in enumerate(tech_companies[:companies_to_process], 1):
        print(f"[{i}/{companies_to_process}] Processing {company.name}...")
        
        try:
            details = service.get_detailed_company_info(company, include_linkedin=True)
            detailed_companies.append(details)
            
            # Show what was found
            info_parts = []
            if details.company_linkedin_url:
                info_parts.append("LinkedIn ✓")
            if details.emails:
                info_parts.append(f"{len(details.emails)} emails")
            if details.employee_profiles:
                info_parts.append(f"{len(details.employee_profiles)} profiles")
            
            if info_parts:
                print(f"  Found: {', '.join(info_parts)}")
            
            # Rate limiting
            time.sleep(random.uniform(2, 4))
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user. Saving results so far...")
            break
        except Exception as e:
            logging.error(f"Error processing {company.name}: {e}")
            continue
    
    # Generate output file
    print(f"\n📝 Generating company list...")
    output_file = "company_list.txt"
    service.generate_company_list(detailed_companies, output_file)
    
    print(f"\n✅ COMPLETE!")
    print(f"📁 Results saved to: {output_file}")
    print(f"📊 Total companies processed: {len(detailed_companies)}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
