"""
Comprehensive Tech Company Search with Ollama AI Verification
==============================================================

This script performs an exhaustive search for ALL IT/SaaS/Software/Cybersecurity
companies within 25km and uses Ollama gemma2:4b to verify relevance.

Features:
- Comprehensive multi-source search (OpenStreetMap, Google Places fallback)
- Mandatory website requirement
- Ollama gemma2:4b AI verification for IT/cyber security relevance
- Product/service description extraction
- Covers all MNCs, startups, and tech companies
- 25km radius from Chennai coordinates

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


class OllamaAIService:
    """Service for interacting with Ollama AI (gemma3:4b)."""
    
    def __init__(self, model: str = "gemma3:4b"):
        self.model = model
        self.base_url = "http://localhost:11434"
        self.logger = logging.getLogger('JobSeeker.OllamaAI')
    
    def test_connection(self) -> bool:
        """Test if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                # Check if gemma3:4b is available
                if any('gemma3' in name and '4b' in name for name in model_names):
                    self.logger.info(f"✓ Ollama is running with {self.model}")
                    return True
                else:
                    self.logger.warning(f"Model {self.model} not found. Available: {model_names}")
                    return False
            return False
        except Exception as e:
            self.logger.error(f"Cannot connect to Ollama: {e}")
            return False
    
    def verify_it_relevance(self, company_name: str, website: str = None, description: str = None) -> Dict:
        """
        Verify if a company provides IT services or cybersecurity services.
        
        Args:
            company_name: Name of the company
            website: Company website URL
            description: Brief description from website
            
        Returns:
            Dict with 'is_relevant' (bool), 'category' (str), 'service_description' (str)
        """
        try:
            # Build context for AI
            context_parts = [f"Company Name: {company_name}"]
            if website:
                context_parts.append(f"Website: {website}")
            if description:
                context_parts.append(f"Description: {description}")
            
            context = "\n".join(context_parts)
            
            prompt = f"""Analyze this company and determine if it provides IT services, software development, SaaS products, or cybersecurity services.

{context}

IMPORTANT: Only mark as relevant if the company provides:
- IT Services (consulting, managed services, infrastructure)
- Software Development (custom software, applications)
- SaaS Products (cloud platforms, subscription software)
- Cybersecurity Services (security consulting, penetration testing, SOC)
- Web/Mobile Development
- Cloud Services
- Data Analytics/AI/ML services
- DevOps/Automation services

DO NOT mark as relevant if the company is:
- Retail stores
- Restaurants/Food services
- Furniture/Home goods
- General trading
- Manufacturing (unless IT/software focused)
- Real estate
- Healthcare (unless health-tech software)

Respond in JSON format:
{{
    "is_relevant": true/false,
    "category": "IT Services/Software Development/SaaS/Cybersecurity/Cloud Services/Web Development/Not Relevant",
    "service_description": "One-line description of their main IT/tech product or service"
}}"""

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '{}')
                
                try:
                    data = json.loads(response_text)
                    return {
                        'is_relevant': data.get('is_relevant', False),
                        'category': data.get('category', 'Unknown'),
                        'service_description': data.get('service_description', 'N/A')
                    }
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse Ollama response for {company_name}: {e}")
                    self.logger.debug(f"Response was: {response_text}")
                    return {'is_relevant': False, 'category': 'Unknown', 'service_description': 'N/A'}
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return {'is_relevant': False, 'category': 'Unknown', 'service_description': 'N/A'}
                
        except Exception as e:
            self.logger.error(f"Error verifying {company_name}: {e}")
            return {'is_relevant': False, 'category': 'Unknown', 'service_description': 'N/A'}


def extract_website_info(website: str) -> Dict[str, str]:
    """
    Extract description and other info from company website.
    
    Args:
        website: Company website URL
        
    Returns:
        Dict with 'description', 'title', 'keywords'
    """
    try:
        # Ensure URL has protocol
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(website, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ''
        
        # Extract meta description
        description = ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            description = meta_desc['content'].strip()
        
        # Try og:description if no meta description
        if not description:
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc and og_desc.get('content'):
                description = og_desc['content'].strip()
        
        # Try to find description in page content
        if not description:
            # Look for common description patterns
            for selector in ['p.description', 'div.description', 'section.about p']:
                elem = soup.select_one(selector)
                if elem:
                    description = elem.get_text().strip()[:300]
                    break
        
        # Fallback: get first substantial paragraph
        if not description:
            paragraphs = soup.find_all('p')
            for p in paragraphs[:5]:
                text = p.get_text().strip()
                if len(text) > 50:
                    description = text[:300]
                    break
        
        # Extract keywords
        keywords = ''
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = meta_keywords['content'].strip()
        
        return {
            'description': description or 'N/A',
            'title': title_text or 'N/A',
            'keywords': keywords or 'N/A'
        }
        
    except Exception as e:
        logging.debug(f"Error extracting info from {website}: {e}")
        return {
            'description': 'N/A',
            'title': 'N/A',
            'keywords': 'N/A'
        }


def verify_website_exists(website: str) -> bool:
    """
    Verify that a website actually exists and is accessible.
    
    Args:
        website: Website URL to verify
        
    Returns:
        bool: True if website is accessible, False otherwise
    """
    try:
        if not website:
            return False
        
        # Ensure URL has protocol
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(website, headers=headers, timeout=10, allow_redirects=True)
        
        # Accept 2xx and 3xx status codes
        return response.status_code < 400
        
    except:
        return False


def search_comprehensive_companies(location: Location, radius_km: float) -> List[Company]:
    """
    Perform comprehensive search using multiple strategies.
    
    Args:
        location: Center location for search
        radius_km: Search radius in kilometers
        
    Returns:
        List of all companies found
    """
    logger = logging.getLogger('JobSeeker.ComprehensiveSearch')
    company_service = CompanySearchService()
    
    logger.info(f"Starting comprehensive search within {radius_km}km...")
    
    # Use the existing search service
    all_companies = company_service.search_companies(location, radius_km)
    
    logger.info(f"Found {len(all_companies)} companies from OpenStreetMap")
    
    return all_companies


def main():
    """Main execution function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/comprehensive_search.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('JobSeeker.Main')
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TECH COMPANY SEARCH WITH AI VERIFICATION")
    print("=" * 80)
    
    # Coordinates: 13°01'10.3"N 80°06'58.6"E (Chennai area)
    latitude = 13.0195278
    longitude = 80.1162778
    radius_km = 25.0
    
    print(f"\n📍 Search Location: {latitude}°N, {longitude}°E")
    print(f"📏 Search Radius: {radius_km} km")
    print(f"🤖 AI Model: Ollama gemma3:4b")
    print(f"🎯 Focus: IT Services & Cybersecurity ONLY")
    print(f"✅ Requirement: Must have working website\n")
    
    # Initialize services
    location_service = LocationService()
    ollama_service = OllamaAIService()
    
    # Test Ollama connection
    print("🔍 Testing Ollama connection...")
    if not ollama_service.test_connection():
        print("\n❌ ERROR: Cannot connect to Ollama or gemma3:4b model not found")
        print("Please ensure:")
        print("  1. Ollama is running: ollama serve")
        print("  2. gemma3:4b model is installed: ollama pull gemma3:4b")
        return
    
    print("✓ Ollama is ready\n")
    
    # Get location info
    print("🔍 Detecting location...")
    location = location_service.reverse_geocode(latitude, longitude)
    print(f"✓ Location: {location.address}\n")
    
    # Comprehensive company search
    print(f"🔍 Searching for ALL companies within {radius_km}km...")
    print("⏱️  This may take a few minutes...\n")
    
    all_companies = search_comprehensive_companies(location, radius_km)
    print(f"✓ Found {len(all_companies)} total companies\n")
    
    # Filter: Must have website
    print("🔍 Filtering companies with websites...")
    companies_with_websites = []
    
    for company in all_companies:
        if company.website and verify_website_exists(company.website):
            companies_with_websites.append(company)
    
    print(f"✓ {len(companies_with_websites)} companies have valid websites\n")
    
    # Broad tech keyword filter (initial filter to reduce AI calls)
    print("🔍 Applying initial tech keyword filter...")
    tech_keywords = [
        'software', 'technology', 'tech', 'it', 'computer', 'digital', 'cyber', 'security',
        'development', 'developer', 'web', 'mobile', 'cloud', 'data', 'saas', 'platform',
        'solution', 'solutions', 'system', 'systems', 'network', 'service', 'services',
        'innovation', 'labs', 'studio', 'online', 'internet', 'app', 'api', 'ai', 'ml',
        'analytics', 'consulting', 'automation', 'infotech', 'technologies', 'devops',
        'erp', 'crm', 'enterprise', 'blockchain', 'iot', 'robotics', 'fintech', 'healthtech'
    ]
    
    potential_tech_companies = []
    for company in companies_with_websites:
        company_text = f"{company.name} {company.category}".lower()
        if any(keyword in company_text for keyword in tech_keywords):
            potential_tech_companies.append(company)
    
    print(f"✓ {len(potential_tech_companies)} potential tech companies identified\n")
    
    # AI-powered verification
    print(f"🤖 Using Ollama gemma3:4b to verify IT/Cybersecurity relevance...")
    print(f"⏱️  Processing {len(potential_tech_companies)} companies...")
    print("    This will take a while...\n")
    
    verified_companies = []
    processed = 0
    
    for i, company in enumerate(potential_tech_companies, 1):
        print(f"[{i}/{len(potential_tech_companies)}] Analyzing: {company.name}")
        
        # Extract website information
        website_info = extract_website_info(company.website)
        
        # Verify with AI
        ai_result = ollama_service.verify_it_relevance(
            company.name,
            company.website,
            website_info['description']
        )
        
        if ai_result['is_relevant']:
            verified_companies.append({
                'company': company,
                'category': ai_result['category'],
                'service_description': ai_result['service_description'],
                'website_info': website_info
            })
            print(f"  ✓ RELEVANT: {ai_result['category']}")
            print(f"    Service: {ai_result['service_description'][:70]}...")
        else:
            print(f"  ✗ Not relevant: {ai_result['category']}")
        
        processed += 1
        
        # Rate limiting to avoid overwhelming Ollama
        time.sleep(random.uniform(1.5, 2.5))
        
        # Progress update every 10 companies
        if processed % 10 == 0:
            print(f"\n📊 Progress: {processed}/{len(potential_tech_companies)} processed, {len(verified_companies)} verified\n")
    
    print(f"\n✅ AI Verification Complete!")
    print(f"📊 Found {len(verified_companies)} verified IT/Cybersecurity companies!\n")
    
    # Sort by distance
    verified_companies.sort(key=lambda x: x['company'].distance_km)
    
    # Generate output file
    output_file = "company_list.txt"
    print(f"📝 Generating comprehensive company list...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("IT & CYBERSECURITY COMPANIES - AI-VERIFIED COMPREHENSIVE LIST\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Location: {location.address}\n")
        f.write(f"Coordinates: {latitude}°N, {longitude}°E\n")
        f.write(f"Search Radius: {radius_km} km\n")
        f.write(f"Total Companies Found: {len(verified_companies)}\n")
        f.write(f"AI Model: Ollama gemma3:4b\n")
        f.write(f"Verification: All companies verified for IT/Cybersecurity relevance\n")
        f.write(f"Website Requirement: All companies have verified working websites\n")
        f.write("=" * 80 + "\n\n")
        
        # Company listings
        for i, item in enumerate(verified_companies, 1):
            company = item['company']
            
            f.write(f"\n[{i}] " + "=" * 75 + "\n")
            f.write(f"COMPANY: {company.name}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Category: {item['category']}\n")
            f.write(f"Distance: {company.distance_km:.2f} km from search center\n")
            f.write(f"\nProduct/Service:\n{item['service_description']}\n")
            f.write(f"\nWebsite: {company.website}\n")
            f.write(f"\nAddress: {company.address}\n")
            
            if company.phone:
                f.write(f"Phone: {company.phone}\n")
            
            if company.additional_info.get('email'):
                f.write(f"Email: {company.additional_info['email']}\n")
            
            f.write(f"\nCoordinates: {company.location.latitude}, {company.location.longitude}\n")
            
            # Additional website info
            if item['website_info']['title'] != 'N/A':
                f.write(f"\nWebsite Title: {item['website_info']['title']}\n")
            
            f.write("\n")
    
    print(f"\n✅ SEARCH COMPLETE!")
    print(f"📁 Results saved to: {output_file}")
    print(f"📊 Statistics:")
    print(f"   - Total companies scanned: {len(all_companies)}")
    print(f"   - Companies with websites: {len(companies_with_websites)}")
    print(f"   - Potential tech companies: {len(potential_tech_companies)}")
    print(f"   - AI-verified IT/Cyber companies: {len(verified_companies)}")
    print(f"\n🎯 All companies are:")
    print(f"   ✓ Within {radius_km}km radius")
    print(f"   ✓ Have verified working websites")
    print(f"   ✓ AI-verified for IT/Cybersecurity relevance")
    print(f"   ✓ Include product/service descriptions")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
