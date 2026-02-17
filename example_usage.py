"""
Example Usage Script for Job Seeker Application
================================================

This script demonstrates how to use the Job Seeker modules
programmatically without the interactive CLI.

Author: Job Seeker Team
Date: 2026-02-15
"""

from location_service import LocationService, Location
from company_search import CompanySearchService
from linkedin_scraper import LinkedInScraperService
import json


def example_basic_usage():
    """
    Example 1: Basic usage with automatic location detection.
    """
    print("=== Example 1: Basic Usage ===\n")
    
    # Initialize services
    location_service = LocationService()
    company_service = CompanySearchService()
    
    # Get current location
    location = location_service.get_current_location()
    print(f"Current location: {location}\n")
    
    # Search for companies within 10km
    companies = company_service.search_companies(location, radius_km=10.0)
    print(f"Found {len(companies)} companies\n")
    
    # Display top 5
    for i, company in enumerate(companies[:5], 1):
        print(f"{i}. {company}")


def example_manual_location():
    """
    Example 2: Using manual location input.
    """
    print("\n=== Example 2: Manual Location ===\n")
    
    # Initialize service
    location_service = LocationService()
    
    # Geocode a specific address
    location = location_service.geocode_address("Dubai, UAE")
    print(f"Geocoded location: {location}\n")
    
    # Search companies
    company_service = CompanySearchService()
    companies = company_service.search_companies(location, radius_km=5.0)
    
    print(f"Found {len(companies)} companies within 5km of Dubai")


def example_with_linkedin():
    """
    Example 3: Including LinkedIn profile search.
    """
    print("\n=== Example 3: With LinkedIn Profiles ===\n")
    
    # Setup
    location_service = LocationService()
    company_service = CompanySearchService()
    
    # Get location
    location = location_service.geocode_address("Chennai, India")
    
    # Search companies
    companies = company_service.search_companies(location, radius_km=15.0)
    print(f"Found {len(companies)} companies\n")
    
    # Get LinkedIn profiles for top 3 companies
    linkedin_service = LinkedInScraperService(headless=True)
    
    for company in companies[:3]:
        print(f"Searching LinkedIn for {company.name}...")
        profiles = linkedin_service.search_company_employees(
            company.name,
            max_profiles=3
        )
        print(f"  Found {len(profiles)} profiles\n")
        
        for profile in profiles:
            print(f"    - {profile.name}: {profile.title}")
    
    # Cleanup
    del linkedin_service


def example_export_to_json():
    """
    Example 4: Export results to JSON.
    """
    print("\n=== Example 4: Export to JSON ===\n")
    
    # Get data
    location_service = LocationService()
    company_service = CompanySearchService()
    
    location = location_service.geocode_address("Sydney, Australia")
    companies = company_service.search_companies(location, radius_km=20.0)
    
    # Convert to dict
    companies_data = [company.to_dict() for company in companies]
    
    # Save to JSON
    with open('example_output.json', 'w') as f:
        json.dump(companies_data, f, indent=2)
    
    print(f"Exported {len(companies)} companies to example_output.json")


if __name__ == "__main__":
    # Run examples
    example_basic_usage()
    example_manual_location()
    # example_with_linkedin()  # Uncomment to test LinkedIn scraping
    example_export_to_json()
    
    print("\n✅ All examples completed!")
