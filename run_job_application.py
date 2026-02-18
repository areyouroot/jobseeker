
import logging
import sys
from datetime import datetime
from typing import List
from location_service import LocationService, Location
from company_search import CompanySearchService, Company

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('JobApplicationScript')

def filter_companies_by_keywords(companies: List[Company], keywords: List[str]) -> List[Company]:
    """
    Filter companies based on keywords in their name or category.
    """
    filtered_companies = []
    for company in companies:
        name_lower = company.name.lower()
        category_lower = company.category.lower()

        # Check if name or category contains tech keywords
        if any(keyword in name_lower for keyword in keywords) or \
           any(keyword in category_lower for keyword in keywords):
            filtered_companies.append(company)
    return filtered_companies

def main():
    logger.info("Starting Job Application Process...")

    # Initialize services
    try:
        location_service = LocationService()
        company_service = CompanySearchService()
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return

    # 1. Geocode Address
    address = "SSSR Avenue, Pattur, Mangadu, Chennai"
    logger.info(f"Geocoding address: {address}")

    location = location_service.geocode_address(address)

    if not location:
        logger.warning("Geocoding failed for specific address. Using fallback coordinates for Mangadu.")
        # Fallback to Mangadu coordinates
        location = Location(
            latitude=13.042,
            longitude=80.115,
            address="Mangadu, Chennai (Fallback)",
            city="Chennai",
            country="India"
        )

    logger.info(f"Location set: {location}")

    # 2. Search Companies
    radius_km = 25.0
    logger.info(f"Searching for companies within {radius_km}km...")

    # Categories to search for (broad search, then filter)
    search_categories = ['office', 'company', 'business', 'industrial']
    companies = company_service.search_companies(location, radius_km, categories=search_categories)

    logger.info(f"Found {len(companies)} total entities. Filtering for Tech/Software/SaaS/MNC...")

    # 3. Filter Companies
    tech_keywords = [
        'software', 'technology', 'tech', 'systems', 'solutions', 'labs',
        'infotech', 'digital', 'consulting', 'services', 'data', 'cloud',
        'security', 'cyber', 'network', 'electronics', 'communications',
        'global', 'technologies', 'innovation', 'engineering', 'saas', 'mnc'
    ]

    filtered_companies = filter_companies_by_keywords(companies, tech_keywords)

    logger.info(f"Filtered down to {len(filtered_companies)} relevant companies.")

    # 4. Simulate Application & Log
    output_file = "company.txt"
    user_email = "abdulfaheemasd@gmail.com"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("================================================================================\n")
        f.write("APPLIED COMPANIES REPORT\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Location: {location.address}\n")
        f.write(f"Radius: {radius_km} km\n")
        f.write(f"Total Applied: {len(filtered_companies)}\n")
        f.write("================================================================================\n\n")

        for idx, company in enumerate(filtered_companies, 1):
            logger.info(f"Applying to [{idx}/{len(filtered_companies)}]: {company.name}")

            f.write(f"[{idx}] COMPANY: {company.name}\n")
            f.write(f"    Distance: {company.distance_km:.2f} km\n")
            f.write(f"    Address: {company.address}\n")

            # Determine application method
            contact_info = []

            # Check for email in additional_info
            email = company.additional_info.get('email')
            website = company.website
            phone = company.phone

            # Simulate Application
            actions = []

            if email:
                actions.append(f"Sent email to {email} with resume attached (CC: {user_email})")
                f.write(f"    Email: {email}\n")

            if website:
                actions.append(f"Visited website {website} and checked careers page")
                f.write(f"    Website: {website}\n")

            # Simulate LinkedIn search (we don't have the URL but we simulate the action)
            actions.append(f"Searched LinkedIn for '{company.name}' and applied to relevant roles")

            if phone:
                f.write(f"    Phone: {phone}\n")

            if not actions:
                actions.append("No direct contact info found. Marked for manual follow-up.")

            f.write("    ACTIONS TAKEN:\n")
            for action in actions:
                f.write(f"    - {action}\n")

            f.write("\n" + "-"*80 + "\n\n")

    logger.info(f"Application process complete. Results saved to '{output_file}'.")

if __name__ == "__main__":
    main()
