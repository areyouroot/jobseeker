"""
Multi-Source Comprehensive Tech Company Search
==============================================

This script searches for IT/SaaS/Software/Cybersecurity companies from multiple sources:
- OpenStreetMap (current implementation)
- Google Maps/Places API
- LinkedIn company search
- Naukri company listings
- Glassdoor company data

All results are deduplicated, verified with Ollama gemma3:4b AI, and filtered for
IT/cybersecurity relevance.

Author: Job Seeker Team
Date: 2026-02-17
"""

import logging
import time
import random
import json
from datetime import datetime
from typing import List, Dict, Optional, Set
from location_service import LocationService, Location
from company_search import CompanySearchService, Company
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus


class MultiSourceCompanySearch:
    """Search for companies across multiple sources."""
    
    def __init__(self, latitude: float, longitude: float, radius_km: float):
        self.latitude = latitude
        self.longitude = longitude
        self.radius_km = radius_km
        self.logger = logging.getLogger('JobSeeker.MultiSource')
        self.all_companies = {}  # Deduplicated by name
        
    def search_openstreetmap(self) -> List[Company]:
        """Search OpenStreetMap via existing service."""
        self.logger.info("Searching OpenStreetMap...")
        
        location_service = LocationService()
        company_service = CompanySearchService()
        
        location = location_service.reverse_geocode(self.latitude, self.longitude)
        companies = company_service.search_companies(location, self.radius_km)
        
        self.logger.info(f"Found {len(companies)} companies from OpenStreetMap")
        return companies
    
    def search_google_maps(self) -> List[Dict]:
        """
        Search Google Maps for tech companies.
        Note: Requires Google Maps API key in config.
        """
        self.logger.info("Searching Google Maps...")
        
        try:
            from config import config
            
            if not config.google_maps_api_key:
                self.logger.warning("Google Maps API key not configured, skipping...")
                return []
            
            # Search queries for tech companies
            queries = [
                "software company",
                "IT services",
                "cybersecurity company",
                "SaaS company",
                "technology company",
                "web development company",
                "mobile app development"
            ]
            
            companies = []
            base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            
            for query in queries:
                params = {
                    'location': f"{self.latitude},{self.longitude}",
                    'radius': int(self.radius_km * 1000),  # Convert to meters
                    'keyword': query,
                    'key': config.google_maps_api_key
                }
                
                response = requests.get(base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    for place in results:
                        companies.append({
                            'name': place.get('name'),
                            'address': place.get('vicinity'),
                            'latitude': place['geometry']['location']['lat'],
                            'longitude': place['geometry']['location']['lng'],
                            'rating': place.get('rating'),
                            'source': 'Google Maps'
                        })
                    
                    self.logger.info(f"Found {len(results)} companies for query: {query}")
                
                time.sleep(0.5)  # Rate limiting
            
            self.logger.info(f"Total from Google Maps: {len(companies)}")
            return companies
            
        except Exception as e:
            self.logger.error(f"Error searching Google Maps: {e}")
            return []
    
    def search_linkedin(self, city: str = "Chennai") -> List[Dict]:
        """
        Search LinkedIn for companies.
        Note: This uses web scraping and may be rate-limited.
        """
        self.logger.info("Searching LinkedIn...")
        
        try:
            companies = []
            
            # LinkedIn company search URL
            search_queries = [
                "software company Chennai",
                "IT services Chennai",
                "cybersecurity Chennai",
                "SaaS Chennai",
                "technology Chennai"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            for query in search_queries:
                # Use Google to search LinkedIn (more reliable than direct LinkedIn scraping)
                google_url = f"https://www.google.com/search?q=site:linkedin.com/company+{quote_plus(query)}"
                
                try:
                    response = requests.get(google_url, headers=headers, timeout=10)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract LinkedIn company URLs from Google results
                    links = soup.find_all('a', href=re.compile(r'linkedin\.com/company/'))
                    
                    for link in links[:10]:  # Limit to top 10 per query
                        href = link.get('href')
                        # Extract company name from URL or link text
                        company_name = link.get_text().strip()
                        
                        if company_name and len(company_name) > 3:
                            companies.append({
                                'name': company_name,
                                'linkedin_url': href,
                                'source': 'LinkedIn'
                            })
                    
                    time.sleep(random.uniform(2, 4))  # Respectful rate limiting
                    
                except Exception as e:
                    self.logger.debug(f"Error searching LinkedIn for {query}: {e}")
                    continue
            
            self.logger.info(f"Found {len(companies)} companies from LinkedIn")
            return companies
            
        except Exception as e:
            self.logger.error(f"Error in LinkedIn search: {e}")
            return []
    
    def search_naukri(self, city: str = "Chennai") -> List[Dict]:
        """
        Search Naukri for companies.
        Extracts company names from job listings.
        """
        self.logger.info("Searching Naukri...")
        
        try:
            companies = set()
            
            # Naukri search for IT jobs in Chennai
            search_url = f"https://www.naukri.com/it-jobs-in-{city.lower()}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract company names from job listings
            company_elements = soup.find_all('a', class_=re.compile(r'company|companyName'))
            
            for elem in company_elements:
                company_name = elem.get_text().strip()
                if company_name and len(company_name) > 2:
                    companies.add(company_name)
            
            company_list = [{'name': name, 'source': 'Naukri'} for name in companies]
            
            self.logger.info(f"Found {len(company_list)} companies from Naukri")
            return company_list
            
        except Exception as e:
            self.logger.error(f"Error searching Naukri: {e}")
            return []
    
    def search_glassdoor(self, city: str = "Chennai") -> List[Dict]:
        """
        Search Glassdoor for companies.
        """
        self.logger.info("Searching Glassdoor...")
        
        try:
            companies = []
            
            # Glassdoor company search
            search_url = f"https://www.glassdoor.co.in/Explore/browse-companies.htm?overall_rating_low=3&page=1&occ=Software%20%26%20IT%20Services&locId=3378&locType=N"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract company names
            company_elements = soup.find_all('div', class_=re.compile(r'company|employer'))
            
            for elem in company_elements[:50]:  # Limit to top 50
                company_name = elem.get_text().strip()
                if company_name and len(company_name) > 2:
                    companies.append({
                        'name': company_name,
                        'source': 'Glassdoor'
                    })
            
            self.logger.info(f"Found {len(companies)} companies from Glassdoor")
            return companies
            
        except Exception as e:
            self.logger.error(f"Error searching Glassdoor: {e}")
            return []
    
    def deduplicate_companies(self, all_sources: List[Dict]) -> List[Dict]:
        """Deduplicate companies by name (case-insensitive)."""
        unique = {}
        
        for company in all_sources:
            name = company.get('name', '').strip().lower()
            
            if name and name not in unique:
                unique[name] = company
            elif name in unique:
                # Merge data from multiple sources
                existing = unique[name]
                for key, value in company.items():
                    if key not in existing and value:
                        existing[key] = value
                
                # Track sources
                if 'sources' not in existing:
                    existing['sources'] = [existing.get('source', 'Unknown')]
                if company.get('source'):
                    existing['sources'].append(company['source'])
        
        return list(unique.values())


# Import the OllamaAIService and other functions from comprehensive_search.py
from comprehensive_search import (
    OllamaAIService,
    extract_website_info,
    verify_website_exists
)


def main():
    """Main execution function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/multi_source_search.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('JobSeeker.Main')
    
    print("\n" + "=" * 80)
    print("MULTI-SOURCE COMPREHENSIVE TECH COMPANY SEARCH")
    print("=" * 80)
    
    # Coordinates: 13°01'10.3"N 80°06'58.6"E (Chennai area)
    latitude = 13.0195278
    longitude = 80.1162778
    radius_km = 25.0
    
    print(f"\n📍 Search Location: {latitude}°N, {longitude}°E")
    print(f"📏 Search Radius: {radius_km} km")
    print(f"🔍 Sources: OpenStreetMap, Google Maps, LinkedIn, Naukri, Glassdoor")
    print(f"🤖 AI Model: Ollama gemma3:4b")
    print(f"🎯 Focus: IT Services & Cybersecurity ONLY\n")
    
    # Initialize multi-source search
    multi_search = MultiSourceCompanySearch(latitude, longitude, radius_km)
    
    # Search all sources
    print("🔍 Searching multiple sources...")
    print("=" * 80)
    
    all_companies = []
    
    # 1. OpenStreetMap
    print("\n[1/5] Searching OpenStreetMap...")
    osm_companies = multi_search.search_openstreetmap()
    for company in osm_companies:
        all_companies.append({
            'name': company.name,
            'address': company.address,
            'website': company.website,
            'phone': company.phone,
            'latitude': company.location.latitude,
            'longitude': company.location.longitude,
            'distance_km': company.distance_km,
            'source': 'OpenStreetMap'
        })
    
    # 2. Google Maps
    print("\n[2/5] Searching Google Maps...")
    gmaps_companies = multi_search.search_google_maps()
    all_companies.extend(gmaps_companies)
    
    # 3. LinkedIn
    print("\n[3/5] Searching LinkedIn...")
    linkedin_companies = multi_search.search_linkedin()
    all_companies.extend(linkedin_companies)
    
    # 4. Naukri
    print("\n[4/5] Searching Naukri...")
    naukri_companies = multi_search.search_naukri()
    all_companies.extend(naukri_companies)
    
    # 5. Glassdoor
    print("\n[5/5] Searching Glassdoor...")
    glassdoor_companies = multi_search.search_glassdoor()
    all_companies.extend(glassdoor_companies)
    
    print(f"\n✓ Total companies found (all sources): {len(all_companies)}")
    
    # Deduplicate
    print("\n🔍 Deduplicating companies...")
    unique_companies = multi_search.deduplicate_companies(all_companies)
    print(f"✓ Unique companies: {len(unique_companies)}")
    
    # Filter for companies with websites
    print("\n🔍 Filtering for companies with websites...")
    companies_with_websites = [c for c in unique_companies if c.get('website')]
    print(f"✓ Companies with websites: {len(companies_with_websites)}")
    
    # Apply tech keyword filter
    print("\n🔍 Applying tech keyword filter...")
    tech_keywords = [
        'software', 'technology', 'tech', 'it', 'computer', 'digital', 'cyber', 'security',
        'development', 'developer', 'web', 'mobile', 'cloud', 'data', 'saas', 'platform',
        'solution', 'solutions', 'system', 'systems', 'network', 'service', 'services',
        'innovation', 'labs', 'studio', 'online', 'internet', 'app', 'api', 'ai', 'ml',
        'analytics', 'consulting', 'automation', 'infotech', 'technologies', 'devops',
        'erp', 'crm', 'enterprise', 'blockchain', 'iot', 'robotics', 'fintech', 'healthtech'
    ]
    
    potential_tech = []
    for company in companies_with_websites:
        name = company.get('name', '').lower()
        if any(keyword in name for keyword in tech_keywords):
            potential_tech.append(company)
    
    print(f"✓ Potential tech companies: {len(potential_tech)}")
    
    # AI Verification
    print(f"\n🤖 Using Ollama gemma3:4b for AI verification...")
    ollama_service = OllamaAIService()
    
    if not ollama_service.test_connection():
        print("\n❌ ERROR: Cannot connect to Ollama")
        return
    
    verified_companies = []
    
    for i, company in enumerate(potential_tech, 1):
        print(f"\n[{i}/{len(potential_tech)}] Analyzing: {company.get('name')}")
        
        website = company.get('website')
        if website:
            website_info = extract_website_info(website)
            description = website_info['description']
        else:
            description = None
        
        ai_result = ollama_service.verify_it_relevance(
            company.get('name'),
            website,
            description
        )
        
        if ai_result['is_relevant']:
            verified_companies.append({
                **company,
                'category': ai_result['category'],
                'service_description': ai_result['service_description']
            })
            print(f"  ✓ RELEVANT: {ai_result['category']}")
        else:
            print(f"  ✗ Not relevant")
        
        time.sleep(random.uniform(1.5, 2.5))
    
    print(f"\n✅ AI Verification Complete!")
    print(f"📊 Verified IT/Cybersecurity companies: {len(verified_companies)}")
    
    # Generate output
    output_file = "company_list.txt"
    print(f"\n📝 Generating comprehensive company list...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("IT & CYBERSECURITY COMPANIES - MULTI-SOURCE AI-VERIFIED LIST\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Search Radius: {radius_km} km from {latitude}°N, {longitude}°E\n")
        f.write(f"Sources: OpenStreetMap, Google Maps, LinkedIn, Naukri, Glassdoor\n")
        f.write(f"AI Model: Ollama gemma3:4b\n")
        f.write(f"Total Verified Companies: {len(verified_companies)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, company in enumerate(verified_companies, 1):
            f.write(f"\n[{i}] " + "=" * 75 + "\n")
            f.write(f"COMPANY: {company.get('name')}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Category: {company.get('category')}\n")
            f.write(f"Service: {company.get('service_description')}\n")
            
            if company.get('website'):
                f.write(f"\nWebsite: {company['website']}\n")
            if company.get('address'):
                f.write(f"Address: {company['address']}\n")
            if company.get('phone'):
                f.write(f"Phone: {company['phone']}\n")
            if company.get('distance_km'):
                f.write(f"Distance: {company['distance_km']:.2f} km\n")
            
            # Show which sources found this company
            if company.get('sources'):
                f.write(f"\nFound in: {', '.join(company['sources'])}\n")
            elif company.get('source'):
                f.write(f"\nSource: {company['source']}\n")
            
            f.write("\n")
    
    print(f"\n✅ SEARCH COMPLETE!")
    print(f"📁 Results saved to: {output_file}")
    print(f"📊 Total verified companies: {len(verified_companies)}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
