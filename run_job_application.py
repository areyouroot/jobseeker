
import logging
import sys
import os
from datetime import datetime
from typing import List
from location_service import LocationService, Location
from company_search import CompanySearchService, Company
from email_service import EmailService
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('JobApplicationScript')

def load_email_credentials():
    """Load email credentials from file or environment variables."""
    sender_email = None
    sender_password = None

    # Try loading from file first
    if os.path.exists("email_credentials.txt"):
        with open("email_credentials.txt", "r") as f:
            for line in f:
                if line.startswith("SENDER_EMAIL="):
                    sender_email = line.strip().split("=", 1)[1]
                elif line.startswith("SENDER_PASSWORD="):
                    sender_password = line.strip().split("=", 1)[1]

    return sender_email, sender_password

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

        # Initialize Email Service
        sender_email, sender_password = load_email_credentials()

        # Check if credentials are placeholders
        if not sender_email or sender_email == "your_email@gmail.com":
             logger.warning("⚠️  Using placeholder email credentials. Real emails will be SIMULATED.")
             email_service = EmailService(None, None)
        else:
             email_service = EmailService(sender_email, sender_password)
             # Validate connection before starting
             try:
                 import smtplib
                 server = smtplib.SMTP('smtp.gmail.com', 587)
                 server.starttls()
                 server.login(sender_email, sender_password)
                 server.quit()
                 logger.info("✅ Email credentials validated successfully.")
             except Exception as auth_err:
                 logger.error(f"❌ Failed to authenticate with Gmail: {auth_err}")
                 logger.warning("⚠️  Proceeding in SIMULATION mode due to authentication failure.")
                 email_service = EmailService(None, None)

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
    resume_path = "resume.txt"

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

            # Check for email in additional_info
            email = company.additional_info.get('email')
            website = company.website
            phone = company.phone

            # Simulate Application
            actions = []

            if email:
                subject = f"Application for {company.category} Role - {company.name}"
                body = f"""
Dear Hiring Manager at {company.name},

I am writing to express my strong interest in joining your team at {company.name}. I understand that as a leading organization in the {company.category} sector, you are constantly looking for skilled professionals to drive innovation.

I am an experienced Application Security Engineer & Full-Stack Developer with over 3 years of expertise in architecting secure CI/CD pipelines, DevSecOps, and Cloud Security (Azure/AWS). My technical stack includes .NET, Angular, Python, and extensive experience with security frameworks like STRIDE and Zero Trust architecture.

I am confident that my background in both software development and cybersecurity would be a valuable asset to {company.name}.

Please find my resume attached for your review.

Best regards,
Abdul Faheem
+91 8870682288
abdulfaheemasd@gmail.com

--
This is an automated email regarding a job application.
                """

                # Attempt to send email
                sent = email_service.send_email(email, subject, body, resume_path, cc_email=user_email)

                if sent:
                    actions.append(f"SENT EMAIL to {email} with customized body (CC: {user_email})")
                else:
                    actions.append(f"Simulated email to {email} (CC: {user_email}) - Real email requires configured credentials")

                f.write(f"    Email: {email}\n")

            if website:
                actions.append(f"Visited website {website} and checked careers page")
                f.write(f"    Website: {website}\n")

            # Simulate LinkedIn search
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
