"""
Job Seeker - Main Application
==============================

This is the main entry point for the Job Seeker application.
It orchestrates all services to find companies and LinkedIn profiles
within a specified distance from the user's location.

Features:
- Interactive CLI interface
- Location detection
- Company search by distance
- LinkedIn profile retrieval
- Export results to JSON/CSV

Author: Job Seeker Team
Date: 2026-02-15
"""

import logging
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd

# Import our custom services
from config import config
from location_service import LocationService, Location
from company_search import CompanySearchService, Company
from linkedin_scraper import LinkedInScraperService, LinkedInProfile


class JobSeekerApp:
    """
    Main application class for Job Seeker.
    
    This class orchestrates all services and provides a user-friendly
    interface for finding companies and LinkedIn profiles.
    
    Attributes:
        logger (Logger): Application logger
        location_service (LocationService): Service for location operations
        company_service (CompanySearchService): Service for company search
        linkedin_service (LinkedInScraperService): Service for LinkedIn scraping
    """
    
    def __init__(self):
        """
        Initialize the Job Seeker application.
        
        Sets up all required services and validates configuration.
        """
        self.logger = logging.getLogger('JobSeeker.App')
        
        # Validate configuration
        if not config.validate():
            self.logger.error("Configuration validation failed")
            sys.exit(1)
        
        # Initialize services
        self.logger.info("Initializing services...")
        self.location_service = LocationService()
        self.company_service = CompanySearchService()
        self.linkedin_service = None  # Lazy initialization
        
        self.logger.info("Job Seeker application initialized successfully")
    
    def display_banner(self) -> None:
        """
        Display application banner and welcome message.
        """
        banner = """
        ╔═══════════════════════════════════════════════════════╗
        ║                                                       ║
        ║              JOB SEEKER APPLICATION                  ║
        ║         Find Companies & LinkedIn Profiles           ║
        ║              Within Your Area                        ║
        ║                                                       ║
        ╚═══════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def get_search_parameters(self) -> tuple[Location, float]:
        """
        Get search parameters from user interactively.
        
        Returns:
            tuple[Location, float]: User location and search radius
        """
        print("\n" + "="*60)
        print("STEP 1: Determine Your Location")
        print("="*60)
        
        # Get user location
        location = self.location_service.get_location_interactive()
        
        if not location:
            self.logger.error("Failed to determine location")
            sys.exit(1)
        
        print(f"\n✓ Location confirmed: {location}")
        
        # Get search radius
        print("\n" + "="*60)
        print("STEP 2: Set Search Radius")
        print("="*60)
        
        while True:
            try:
                radius_input = input(
                    f"\nEnter search radius in kilometers "
                    f"(default: {config.default_search_radius_km}km): "
                ).strip()
                
                if not radius_input:
                    radius = config.default_search_radius_km
                else:
                    radius = float(radius_input)
                
                if radius <= 0:
                    print("❌ Radius must be positive. Please try again.")
                    continue
                
                if radius > 100:
                    confirm = input(
                        f"⚠️  {radius}km is quite large. Continue? (y/n): "
                    ).strip().lower()
                    if confirm != 'y':
                        continue
                
                break
                
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
        
        print(f"\n✓ Search radius set to: {radius}km")
        return location, radius
    
    def search_companies(
        self,
        location: Location,
        radius: float
    ) -> List[Company]:
        """
        Search for companies within the specified radius.
        
        Args:
            location (Location): Search origin
            radius (float): Search radius in kilometers
            
        Returns:
            List[Company]: List of companies found
        """
        print("\n" + "="*60)
        print("STEP 3: Searching for Companies")
        print("="*60)
        print(f"\n🔍 Searching for companies within {radius}km...")
        
        companies = self.company_service.search_companies(location, radius)
        
        if not companies:
            print("\n❌ No companies found in the specified area.")
            return []
        
        print(f"\n✓ Found {len(companies)} companies!")
        
        # Display top 10 companies
        print("\n📊 Top 10 Closest Companies:")
        print("-" * 60)
        for i, company in enumerate(companies[:10], 1):
            print(f"{i:2d}. {company.name:30s} | {company.distance_km:6.2f}km | {company.category}")
        
        if len(companies) > 10:
            print(f"\n... and {len(companies) - 10} more companies")
        
        return companies
    
    def get_linkedin_profiles(
        self,
        companies: List[Company],
        max_companies: int = 10
    ) -> Dict[str, List[LinkedInProfile]]:
        """
        Get LinkedIn profiles for employees at the found companies.
        
        Args:
            companies (List[Company]): List of companies
            max_companies (int): Maximum number of companies to process
            
        Returns:
            Dict[str, List[LinkedInProfile]]: Mapping of company name to profiles
        """
        print("\n" + "="*60)
        print("STEP 4: Finding LinkedIn Profiles")
        print("="*60)
        
        # Ask user if they want to proceed
        proceed = input(
            f"\n🔗 Search LinkedIn for employees at these companies? (y/n): "
        ).strip().lower()
        
        if proceed != 'y':
            print("\n⏭️  Skipping LinkedIn search")
            return {}
        
        # Ask about authentication
        use_auth = input(
            "\n🔐 Login to LinkedIn for better results? (y/n): "
        ).strip().lower()
        
        # Initialize LinkedIn service (lazy initialization)
        if self.linkedin_service is None:
            print("\n⚙️  Initializing LinkedIn scraper...")
            self.linkedin_service = LinkedInScraperService()
        
        # Login if requested
        if use_auth == 'y':
            if not self.linkedin_service.login():
                print("\n⚠️  Login failed - continuing without authentication")
        
        # Process companies
        results = {}
        companies_to_process = companies[:max_companies]
        
        print(f"\n🔍 Processing {len(companies_to_process)} companies...")
        print("⏱️  This may take a few minutes due to rate limiting...\n")
        
        for i, company in enumerate(companies_to_process, 1):
            print(f"[{i}/{len(companies_to_process)}] Searching {company.name}...")
            
            try:
                profiles = self.linkedin_service.search_company_employees(
                    company.name,
                    max_profiles=config.max_linkedin_profiles
                )
                
                if profiles:
                    results[company.name] = profiles
                    print(f"  ✓ Found {len(profiles)} profiles")
                else:
                    print(f"  ⚠️  No profiles found")
                    
            except Exception as e:
                self.logger.error(f"Error processing {company.name}: {e}")
                print(f"  ❌ Error occurred")
        
        total_profiles = sum(len(profiles) for profiles in results.values())
        print(f"\n✓ Found {total_profiles} total LinkedIn profiles across {len(results)} companies")
        
        return results
    
    def export_results(
        self,
        companies: List[Company],
        linkedin_profiles: Dict[str, List[LinkedInProfile]]
    ) -> None:
        """
        Export results to JSON and CSV files.
        
        Args:
            companies (List[Company]): List of companies found
            linkedin_profiles (Dict): LinkedIn profiles by company
        """
        print("\n" + "="*60)
        print("STEP 5: Exporting Results")
        print("="*60)
        
        # Create output directory
        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export companies to JSON
        companies_data = [company.to_dict() for company in companies]
        companies_json_path = output_dir / f'companies_{timestamp}.json'
        
        with open(companies_json_path, 'w', encoding='utf-8') as f:
            json.dump(companies_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Companies exported to: {companies_json_path}")
        
        # Export companies to CSV
        companies_csv_path = output_dir / f'companies_{timestamp}.csv'
        df_companies = pd.DataFrame(companies_data)
        df_companies.to_csv(companies_csv_path, index=False, encoding='utf-8')
        
        print(f"✓ Companies exported to: {companies_csv_path}")
        
        # Export LinkedIn profiles if available
        if linkedin_profiles:
            # Flatten profiles data
            profiles_data = []
            for company_name, profiles in linkedin_profiles.items():
                for profile in profiles:
                    profile_dict = profile.to_dict()
                    profiles_data.append(profile_dict)
            
            # Export to JSON
            profiles_json_path = output_dir / f'linkedin_profiles_{timestamp}.json'
            with open(profiles_json_path, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ LinkedIn profiles exported to: {profiles_json_path}")
            
            # Export to CSV
            profiles_csv_path = output_dir / f'linkedin_profiles_{timestamp}.csv'
            df_profiles = pd.DataFrame(profiles_data)
            df_profiles.to_csv(profiles_csv_path, index=False, encoding='utf-8')
            
            print(f"✓ LinkedIn profiles exported to: {profiles_csv_path}")
        
        print(f"\n📁 All results saved in: {output_dir}")
    
    def run(self) -> None:
        """
        Main application workflow.
        
        This method orchestrates the entire application flow:
        1. Display banner
        2. Get search parameters
        3. Search for companies
        4. Get LinkedIn profiles
        5. Export results
        """
        try:
            # Display welcome banner
            self.display_banner()
            
            # Get search parameters
            location, radius = self.get_search_parameters()
            
            # Search for companies
            companies = self.search_companies(location, radius)
            
            if not companies:
                print("\n👋 No companies found. Exiting.")
                return
            
            # Get LinkedIn profiles
            linkedin_profiles = self.get_linkedin_profiles(companies)
            
            # Export results
            self.export_results(companies, linkedin_profiles)
            
            # Success message
            print("\n" + "="*60)
            print("✅ JOB SEEKER COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\n📊 Summary:")
            print(f"  • Companies found: {len(companies)}")
            print(f"  • LinkedIn profiles found: {sum(len(p) for p in linkedin_profiles.values())}")
            print("\n💡 Next steps:")
            print("  • Review the exported CSV/JSON files")
            print("  • Visit company websites and LinkedIn profiles")
            print("  • Prepare your applications!")
            print("\n👋 Good luck with your job search!\n")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Application interrupted by user")
            self.logger.info("Application interrupted by user")
        except Exception as e:
            print(f"\n\n❌ An error occurred: {e}")
            self.logger.error(f"Application error: {e}", exc_info=True)
        finally:
            # Cleanup
            if self.linkedin_service:
                del self.linkedin_service


def main():
    """
    Application entry point.
    """
    app = JobSeekerApp()
    app.run()


if __name__ == "__main__":
    main()
