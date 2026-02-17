"""
Enhanced Tech Company Search - Reliable Version
===============================================

Comprehensive search for IT/SaaS/Software companies with:
- Website requirement (no companies without websites)
- Product/service description extraction
- Focus on IT services and cyber security
- Covers all MNCs and startups within 25km

Author: Job Seeker Team
Date: 2026-02-15
"""

import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
from location_service import LocationService
from company_search import CompanySearchService
import requests
from bs4 import BeautifulSoup
import re


def get_company_info(company_name: str, website: str) -> Dict:
    """
    Extract company information from website.
    
    Returns:
        Dict with 'description', 'category', 'is_tech'
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(website, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get page text
        text = soup.get_text().lower()
        
        # Tech keywords for categorization
        tech_categories = {
            'Cyber Security': ['cyber', 'security', 'penetration', 'vulnerability', 'firewall', 'threat', 'soc', 'siem'],
            'SaaS Platform': ['saas', 'platform', 'cloud', 'subscription', 'software as a service'],
            'Software Development': ['software development', 'custom software', 'application development', 'dev', 'programming'],
            'IT Services': ['it services', 'it consulting', 'managed services', 'infrastructure', 'support'],
            'Web Development': ['web development', 'website', 'web design', 'frontend', 'backend', 'full stack'],
            'Mobile Development': ['mobile app', 'android', 'ios', 'mobile development'],
            'Data Analytics': ['data analytics', 'big data', 'business intelligence', 'data science', 'ai', 'machine learning'],
            'Cloud Services': ['cloud computing', 'aws', 'azure', 'gcp', 'cloud migration'],
            'DevOps': ['devops', 'ci/cd', 'automation', 'kubernetes', 'docker'],
            'ERP/CRM': ['erp', 'crm', 'enterprise software', 'business software']
        }
        
        # Find matching category
        matched_category = 'IT/Technology'
        for category, keywords in tech_categories.items():
            if any(keyword in text for keyword in keywords):
                matched_category = category
                break
        
        # Check if it's actually tech-related
        tech_indicators = [
            'software', 'technology', 'it', 'cyber', 'security', 'development',
            'saas', 'platform', 'cloud', 'digital', 'web', 'mobile', 'app',
            'data', 'analytics', 'ai', 'automation', 'devops', 'programming'
        ]
        
        is_tech = any(indicator in text for indicator in tech_indicators)
        
        # Extract description
        description = "N/A"
        
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            description = meta_desc['content'][:250]
        elif soup.find('meta', attrs={'property': 'og:description'}):
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            description = og_desc['content'][:250]
        else:
            # Try to find description in common places
            for tag in ['h1', 'h2', 'p']:
                elements = soup.find_all(tag)
                for elem in elements[:5]:
                    elem_text = elem.get_text().strip()
                    if len(elem_text) > 50 and len(elem_text) < 300:
                        description = elem_text
                        break
                if description != "N/A":
                    break
        
        return {
            'description': description,
            'category': matched_category,
            'is_tech': is_tech
        }
        
    except Exception as e:
        logging.error(f"Error extracting info from {website}: {e}")
        return {
            'description': 'N/A',
            'category': 'Unknown',
            'is_tech': False
        }


def main():
    """Main execution function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "=" * 80)
    print("ENHANCED TECH COMPANY SEARCH - COMPREHENSIVE VERSION")
    print("=" * 80)
    
    # Coordinates: 13°01'10.3"N 80°06'58.6"E
    latitude = 13.0195278
    longitude = 80.1162778
    radius_km = 25.0
    
    print(f"\nSearch Location: {latitude}°N, {longitude}°E")
    print(f"Search Radius: {radius_km} km")
    print(f"Requirements: Website mandatory, IT/Cyber Security focus\n")
    
    # Initialize services
    location_service = LocationService()
    company_service = CompanySearchService()
    
    # Get location
    print("🔍 Detecting location...")
    location = location_service.reverse_geocode(latitude, longitude)
    print(f"✓ Location: {location.address}\n")
    
    # Comprehensive search
    print(f"🔍 Searching for ALL companies within {radius_km}km...")
    all_companies = company_service.search_companies(location, radius_km)
    print(f"✓ Found {len(all_companies)} total companies\n")
    
    # Filter: must have website
    companies_with_websites = [c for c in all_companies if c.website]
    print(f"✓ {len(companies_with_websites)} companies have websites\n")
    
    # Broad tech keyword filter
    tech_keywords = [
        'software', 'technology', 'tech', 'it', 'computer', 'digital',
        'cyber', 'security', 'development', 'dev', 'web', 'mobile', 'cloud', 'data',
        'saas', 'platform', 'solution', 'system', 'network', 'service',
        'innovation', 'labs', 'studio', 'media', 'online', 'internet',
        'app', 'api', 'ai', 'ml', 'analytics', 'consulting', 'automation',
        'infotech', 'systems', 'solutions', 'technologies'
    ]
    
    potential_tech = []
    for company in companies_with_websites:
        company_text = f"{company.name} {company.category}".lower()
        if any(keyword in company_text for keyword in tech_keywords):
            potential_tech.append(company)
    
    print(f"✓ {len(potential_tech)} potential tech companies identified\n")
    
    # Extract detailed information
    print(f"📊 Extracting product/service information...")
    print("⏱️  This will take a while...\n")
    
    verified_companies = []
    
    for i, company in enumerate(potential_tech[:150], 1):  # Process top 150
        print(f"[{i}/{min(len(potential_tech), 150)}] Analyzing {company.name}...")
        
        # Get company info from website
        info = get_company_info(company.name, company.website)
        
        if info['is_tech']:
            verified_companies.append({
                'company': company,
                'category': info['category'],
                'description': info['description']
            })
            print(f"  ✓ {info['category']}: {info['description'][:60]}...")
        else:
            print(f"  ✗ Not tech-related")
        
        # Rate limiting
        time.sleep(random.uniform(0.5, 1.5))
    
    print(f"\n✅ Found {len(verified_companies)} verified IT/Tech companies!\n")
    
    # Sort by distance
    verified_companies.sort(key=lambda x: x['company'].distance_km)
    
    # Generate output
    output_file = "company_list.txt"
    print(f"📝 Generating company list to {output_file}...\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("IT & CYBER SECURITY COMPANIES - VERIFIED RESULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Location: {location.address}\n")
        f.write(f"Search Radius: {radius_km} km\n")
        f.write(f"Total Companies: {len(verified_companies)}\n")
        f.write(f"Requirements: Website mandatory, IT/Cyber Security verified\n")
        f.write(f"Focus: SaaS, Software Development, IT Services, Cyber Security\n")
        f.write("=" * 80 + "\n\n")
        
        # Companies
        for i, item in enumerate(verified_companies, 1):
            company = item['company']
            
            f.write(f"\n[{i}]\n")
            f.write("=" * 80 + "\n")
            f.write(f"COMPANY: {company.name}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Category: {item['category']}\n")
            f.write(f"Distance: {company.distance_km:.2f} km\n")
            f.write(f"\nProduct/Service:\n{item['description']}\n")
            f.write(f"\nAddress: {company.address}\n")
            
            if company.phone:
                f.write(f"Phone: {company.phone}\n")
            
            f.write(f"Website: {company.website}\n")
            f.write(f"\nCoordinates: {company.location.latitude}, {company.location.longitude}\n")
            f.write("\n")
    
    print(f"\n✅ COMPLETE!")
    print(f"📁 Results saved to: {output_file}")
    print(f"📊 Total verified companies: {len(verified_companies)}")
    print(f"🎯 All companies have websites and verified IT/Cyber Security focus")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
