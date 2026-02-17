"""
Enhanced Tech Company Search with AI Filtering
==============================================

This script performs a comprehensive search for IT/SaaS/Software companies
and uses Ollama AI to verify relevance to IT services and cyber security.

Features:
- Comprehensive search for all tech companies
- Filters companies without websites
- Uses Ollama gemma2:4b to verify IT/cyber security relevance
- Adds product/service descriptions
- Covers MNCs and startups within 25km

Author: Job Seeker Team
Date: 2026-02-15
"""

import logging
import time
import random
import json
from datetime import datetime
from typing import List, Dict, Optional
from location_service import LocationService
from company_search import CompanySearchService
import requests
from bs4 import BeautifulSoup


class OllamaService:
    """Service for interacting with Ollama AI."""
    
    def __init__(self, model: str = "gemma3:4b"):
        self.model = model
        self.base_url = "http://localhost:11434"
        self.logger = logging.getLogger('JobSeeker.Ollama')
    
    def check_relevance(self, company_name: str, website: str = None, description: str = None) -> Dict:
        """
        Check if a company is relevant to IT services or cyber security.
        
        Returns:
            Dict with 'is_relevant' (bool), 'category' (str), 'description' (str)
        """
        try:
            # Build context
            context = f"Company: {company_name}"
            if website:
                context += f"\nWebsite: {website}"
            if description:
                context += f"\nDescription: {description}"
            
            prompt = f"""Analyze this company and determine if it provides IT services, software development, SaaS products, or cyber security services.

{context}

Respond in JSON format:
{{
    "is_relevant": true/false,
    "category": "SaaS/Software Development/IT Services/Cyber Security/Other",
    "description": "Brief description of their main product/service (1 line)"
}}

Only mark as relevant if they provide technology/IT/software/cyber security services. Exclude: retail, furniture, food, general stores, etc."""

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '{}')
                
                # Parse JSON response
                try:
                    data = json.loads(response_text)
                    return {
                        'is_relevant': data.get('is_relevant', False),
                        'category': data.get('category', 'Unknown'),
                        'description': data.get('description', 'N/A')
                    }
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse Ollama response for {company_name}")
                    return {'is_relevant': False, 'category': 'Unknown', 'description': 'N/A'}
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return {'is_relevant': False, 'category': 'Unknown', 'description': 'N/A'}
                
        except Exception as e:
            self.logger.error(f"Error checking relevance for {company_name}: {e}")
            return {'is_relevant': False, 'category': 'Unknown', 'description': 'N/A'}


def get_company_description(website: str) -> str:
    """Extract company description from website."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(website, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'][:200]
        
        # Try og:description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'][:200]
        
        # Try first paragraph
        paragraphs = soup.find_all('p')
        for p in paragraphs[:3]:
            text = p.get_text().strip()
            if len(text) > 50:
                return text[:200]
        
        return "N/A"
    except:
        return "N/A"


def main():
    """Main execution function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "=" * 80)
    print("ENHANCED TECH COMPANY SEARCH WITH AI FILTERING")
    print("=" * 80)
    
    # Coordinates: 13°01'10.3"N 80°06'58.6"E
    latitude = 13.0195278
    longitude = 80.1162778
    radius_km = 25.0
    
    print(f"\nSearch Location: {latitude}°N, {longitude}°E")
    print(f"Search Radius: {radius_km} km")
    print(f"AI Model: Ollama gemma3:4b\n")
    
    # Initialize services
    location_service = LocationService()
    company_service = CompanySearchService()
    ollama_service = OllamaService()
    
    # Test Ollama connection
    print("🔍 Testing Ollama connection...")
    try:
        test_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if test_response.status_code == 200:
            print("✓ Ollama is running\n")
        else:
            print("❌ Ollama is not responding. Please start Ollama first.")
            return
    except:
        print("❌ Cannot connect to Ollama. Please ensure Ollama is running.")
        print("   Run: ollama serve")
        return
    
    # Get location
    print("🔍 Detecting location...")
    location = location_service.reverse_geocode(latitude, longitude)
    print(f"✓ Location: {location.address}\n")
    
    # Comprehensive search with expanded keywords
    print(f"🔍 Searching for ALL companies within {radius_km}km...")
    all_companies = company_service.search_companies(location, radius_km)
    print(f"✓ Found {len(all_companies)} total companies\n")
    
    # Filter for potential tech companies (broad initial filter)
    tech_keywords = [
        'software', 'technology', 'tech', 'it', 'computer', 'digital',
        'cyber', 'security', 'development', 'web', 'mobile', 'cloud', 'data',
        'saas', 'platform', 'solution', 'system', 'network', 'service',
        'innovation', 'labs', 'studio', 'media', 'online', 'internet',
        'app', 'api', 'ai', 'ml', 'analytics', 'consulting', 'automation'
    ]
    
    potential_tech = []
    for company in all_companies:
        # Must have a website
        if not company.website:
            continue
        
        company_text = f"{company.name} {company.category}".lower()
        
        # Check for tech keywords OR if category suggests tech
        is_potential = (
            any(keyword in company_text for keyword in tech_keywords) or
            company.category in ['it', 'office', 'company', 'industrial', 'commercial', 'business']
        )
        
        if is_potential:
            potential_tech.append(company)
    
    print(f"✓ Found {len(potential_tech)} potential tech companies with websites\n")
    
    # AI-powered filtering
    print(f"🤖 Using AI to verify IT/Cyber Security relevance...")
    print("⏱️  This will take a while...\n")
    
    verified_companies = []
    
    for i, company in enumerate(potential_tech[:200], 1):  # Process top 200
        print(f"[{i}/{min(len(potential_tech), 200)}] Analyzing {company.name}...")
        
        # Get website description
        description = get_company_description(company.website) if company.website else None
        
        # Check with AI
        ai_result = ollama_service.check_relevance(
            company.name,
            company.website,
            description
        )
        
        if ai_result['is_relevant']:
            verified_companies.append({
                'company': company,
                'category': ai_result['category'],
                'description': ai_result['description']
            })
            print(f"  ✓ Relevant: {ai_result['category']} - {ai_result['description'][:60]}...")
        else:
            print(f"  ✗ Not relevant: {ai_result['category']}")
        
        # Rate limiting
        time.sleep(random.uniform(1, 2))
    
    print(f"\n✅ Found {len(verified_companies)} verified IT/Cyber Security companies!\n")
    
    # Generate output
    output_file = "company_list.txt"
    print(f"📝 Generating company list to {output_file}...\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("IT & CYBER SECURITY COMPANIES - AI-VERIFIED RESULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Location: {location.address}\n")
        f.write(f"Search Radius: {radius_km} km\n")
        f.write(f"Total Companies: {len(verified_companies)}\n")
        f.write(f"AI Model: Ollama gemma3:4b\n")
        f.write(f"Focus: IT Services, SaaS, Software Development, Cyber Security\n")
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
            f.write(f"\nProduct/Service: {item['description']}\n")
            f.write(f"\nAddress: {company.address}\n")
            
            if company.phone:
                f.write(f"Phone: {company.phone}\n")
            
            f.write(f"Website: {company.website}\n")
            f.write(f"\nCoordinates: {company.location.latitude}, {company.location.longitude}\n")
            f.write("\n")
    
    print(f"\n✅ COMPLETE!")
    print(f"📁 Results saved to: {output_file}")
    print(f"📊 Total verified companies: {len(verified_companies)}")
    print(f"🎯 All companies have websites and are AI-verified for IT/Cyber Security relevance")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
