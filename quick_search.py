"""
Quick Tech Company Search - Fast Version
=========================================

This script quickly searches for tech companies without LinkedIn scraping.
It generates a company list with:
- Company name and address
- Distance from location
- Contact information (if available)
- Company LinkedIn URL (via Google search)

Author: Job Seeker Team
Date: 2026-02-15
"""

import logging
import time
import random
from datetime import datetime
from location_service import LocationService
from company_search import CompanySearchService
import requests
from bs4 import BeautifulSoup


def find_company_linkedin(company_name):
    """Find LinkedIn company page URL via Google search."""
    try:
        search_query = f"{company_name} linkedin company"
        search_url = f"https://www.google.com/search?q={search_query}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'linkedin.com/company/' in href:
                if 'url?q=' in href:
                    url = href.split('url?q=')[1].split('&')[0]
                else:
                    url = href
                return url
        return None
    except:
        return None


def main():
    """Main execution function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "=" * 80)
    print("QUICK TECH COMPANY SEARCH")
    print("=" * 80)
    
    # Coordinates: 13°01'10.3"N 80°06'58.6"E
    latitude = 13.0195278
    longitude = 80.1162778
    radius_km = 25.0
    
    print(f"\nSearch Location: {latitude}°N, {longitude}°E")
    print(f"Search Radius: {radius_km} km\n")
    
    # Initialize services
    location_service = LocationService()
    company_service = CompanySearchService()
    
    # Get location
    print("🔍 Detecting location...")
    location = location_service.reverse_geocode(latitude, longitude)
    print(f"✓ Location: {location.address}\n")
    
    # Search companies
    print(f"🔍 Searching for companies within {radius_km}km...")
    all_companies = company_service.search_companies(location, radius_km)
    print(f"✓ Found {len(all_companies)} total companies\n")
    
    # Filter for tech/office companies
    tech_keywords = ['software', 'technology', 'tech', 'it', 'computer', 'digital',
                     'cyber', 'security', 'development', 'web', 'mobile', 'cloud', 'data']
    
    tech_companies = []
    for company in all_companies:
        company_text = f"{company.name} {company.category}".lower()
        is_tech = any(keyword in company_text for keyword in tech_keywords)
        is_office = company.category in ['office', 'industrial', 'commercial', 'business']
        
        if is_tech or is_office:
            tech_companies.append(company)
    
    print(f"✓ Found {len(tech_companies)} potential tech companies\n")
    
    # Generate company list
    output_file = "company_list.txt"
    print(f"📝 Generating company list to {output_file}...\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("TECH COMPANIES - JOB SEARCH RESULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Location: {location.address}\n")
        f.write(f"Search Radius: {radius_km} km\n")
        f.write(f"Total Companies: {len(tech_companies)}\n")
        f.write(f"Focus: IT, Tech, Cyber Security & Full Stack Development\n")
        f.write("=" * 80 + "\n\n")
        
        # Process companies
        for i, company in enumerate(tech_companies[:100], 1):  # Top 100
            print(f"[{i}/{min(len(tech_companies), 100)}] Processing {company.name}...")
            
            f.write(f"\n[{i}]\n")
            f.write("=" * 80 + "\n")
            f.write(f"COMPANY: {company.name}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Category: {company.category}\n")
            f.write(f"Distance: {company.distance_km:.2f} km\n")
            f.write(f"Address: {company.address}\n")
            
            if company.phone:
                f.write(f"Phone: {company.phone}\n")
            
            if company.website:
                f.write(f"Website: {company.website}\n")
            
            # Try to find LinkedIn
            linkedin_url = find_company_linkedin(company.name)
            if linkedin_url:
                f.write(f"LinkedIn: {linkedin_url}\n")
                print(f"  Found LinkedIn: {linkedin_url}")
            
            f.write(f"\nCoordinates: {company.location.latitude}, {company.location.longitude}\n")
            f.write("\n")
            
            # Rate limiting
            time.sleep(random.uniform(0.5, 1.5))
    
    print(f"\n✅ COMPLETE!")
    print(f"📁 Results saved to: {output_file}")
    print(f"📊 Total companies: {len(tech_companies)}")
    print(f"📝 Processed: {min(len(tech_companies), 100)} companies")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
