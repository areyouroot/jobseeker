# Job Seeker Application 🔍

A Python application that helps you find companies within a specified distance from your location and retrieves LinkedIn profiles of employees at those companies.

## Features ✨

- **📍 Location Detection**: Automatic IP-based geolocation or manual location input
- **🏢 Company Search**: Find companies within a specified radius using OpenStreetMap data
- **💼 LinkedIn Integration**: Retrieve up to 5 LinkedIn profiles per company
- **📊 Data Export**: Export results to JSON and CSV formats
- **🎨 Interactive CLI**: User-friendly command-line interface
- **⚙️ Configurable**: Customizable search parameters and settings
- **🔒 Respectful Scraping**: Built-in rate limiting and ethical scraping practices

## Architecture 🏗️

The application follows **Object-Oriented Programming (OOP)** principles with the following modules:

```
jobseeker/
├── config.py                 # Configuration management (Singleton pattern)
├── location_service.py       # Location detection and geocoding
├── company_search.py         # Company search using Overpass API
├── linkedin_scraper.py       # LinkedIn profile scraping with Selenium
├── main.py                   # Main application orchestrator
├── requirements.txt          # Python dependencies
├── .env.example             # Environment configuration template
└── output/                  # Generated results (JSON/CSV)
```

### Key Classes

- **`Config`**: Singleton class managing all application settings
- **`Location`**: Data class representing geographic coordinates
- **`LocationService`**: Service for geolocation and geocoding operations
- **`Company`**: Data class representing a business entity
- **`CompanySearchService`**: Service for searching companies by location
- **`LinkedInProfile`**: Data class representing a LinkedIn profile
- **`LinkedInScraperService`**: Service for scraping LinkedIn profiles
- **`JobSeekerApp`**: Main application orchestrator

## Installation 📦

### Prerequisites

- Python 3.8 or higher
- Google Chrome browser (for LinkedIn scraping)
- Internet connection

### Setup Steps

1. **Clone or navigate to the project directory**:
   ```bash
   cd z:\git\Personal\jobseeker
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env and add your credentials (optional)
   # - GOOGLE_MAPS_API_KEY (optional - for enhanced location services)
   # - LINKEDIN_EMAIL (optional - for authenticated LinkedIn access)
   # - LINKEDIN_PASSWORD (optional)
   ```

## Usage 🚀

### Basic Usage

Run the application:

```bash
python main.py
```

The application will guide you through an interactive process:

1. **Location Detection**: Choose how to determine your location
   - Auto-detect using IP address (recommended)
   - Enter city/address manually
   - Enter coordinates manually

2. **Set Search Radius**: Specify the distance in kilometers

3. **Company Search**: The app searches for companies within your radius

4. **LinkedIn Profiles**: Optionally search for employee profiles
   - Choose whether to login to LinkedIn
   - Retrieves up to 5 profiles per company

5. **Export Results**: Data is automatically saved to the `output/` folder

### Example Session

```
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║              JOB SEEKER APPLICATION                  ║
║         Find Companies & LinkedIn Profiles           ║
║              Within Your Area                        ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝

============================================================
STEP 1: Determine Your Location
============================================================

=== Location Detection ===
1. Auto-detect using IP address (recommended)
2. Enter city/address manually
3. Enter coordinates manually

Select option (1-3): 1

✓ Location detected: Dubai, UAE (25.2048, 55.2708)

============================================================
STEP 2: Set Search Radius
============================================================

Enter search radius in kilometers (default: 10km): 15

✓ Search radius set to: 15km

============================================================
STEP 3: Searching for Companies
============================================================

🔍 Searching for companies within 15km...

✓ Found 47 companies!

📊 Top 10 Closest Companies:
------------------------------------------------------------
 1. Emirates NBD                  |   2.34km | bank
 2. Dubai Mall                    |   3.12km | shopping_centre
 3. Burj Khalifa                  |   3.45km | office
...
```

## Configuration ⚙️

### Environment Variables

Edit the `.env` file to customize settings:

```bash
# Google Maps API Key (optional)
GOOGLE_MAPS_API_KEY=your_api_key_here

# LinkedIn Credentials (optional)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Application Settings
MAX_LINKEDIN_PROFILES=5
DEFAULT_SEARCH_RADIUS_KM=10
RATE_LIMIT_REQUESTS_PER_MINUTE=10
HEADLESS_BROWSER=True
LOG_LEVEL=INFO
```

### Logging

Logs are saved to `logs/jobseeker.log` with color-coded console output:
- 🔵 DEBUG: Detailed debugging information
- 🟢 INFO: General informational messages
- 🟡 WARNING: Warning messages
- 🔴 ERROR: Error messages
- ⚪ CRITICAL: Critical errors

## Output Format 📄

Results are exported to the `output/` directory with timestamps:

### Companies JSON
```json
[
  {
    "name": "Emirates NBD",
    "category": "bank",
    "address": "Sheikh Zayed Road, Dubai",
    "phone": "+971-4-1234567",
    "website": "https://www.emiratesnbd.com",
    "distance_km": 2.34,
    "latitude": 25.2156,
    "longitude": 55.2803
  }
]
```

### LinkedIn Profiles JSON
```json
[
  {
    "name": "John Doe",
    "title": "Software Engineer",
    "company": "Emirates NBD",
    "location": "Dubai, UAE",
    "profile_url": "https://linkedin.com/in/johndoe",
    "headline": "Software Engineer at Emirates NBD",
    "connections": "500+"
  }
]
```

## Important Notes ⚠️

### LinkedIn Scraping

- **Terms of Service**: LinkedIn's ToS restricts automated scraping. Use responsibly.
- **Rate Limiting**: Built-in delays prevent overwhelming LinkedIn's servers
- **Authentication**: Logging in provides better results but is optional
- **Alternatives**: Consider using LinkedIn's official API for production use

### API Limits

- **OpenStreetMap Overpass API**: Free but rate-limited (1 request/second)
- **IP Geolocation**: Free but less accurate than GPS
- **Google Maps API**: Optional, requires API key and billing account

## Troubleshooting 🔧

### Common Issues

1. **ChromeDriver Error**:
   ```
   Error: ChromeDriver not found
   ```
   **Solution**: The app auto-downloads ChromeDriver. Ensure Chrome is installed.

2. **No Companies Found**:
   ```
   No companies found in the specified area
   ```
   **Solution**: Try increasing the search radius or checking your location.

3. **LinkedIn Login Failed**:
   ```
   Login may have failed - check credentials
   ```
   **Solution**: Verify credentials in `.env` or skip authentication.

4. **Rate Limit Exceeded**:
   ```
   API request failed: 429 Too Many Requests
   ```
   **Solution**: Wait a few minutes before trying again.

## Development 👨‍💻

### Code Structure

The application follows OOP principles with:
- **Encapsulation**: Each service is self-contained
- **Abstraction**: Clear interfaces for each service
- **Inheritance**: Data classes inherit from base classes
- **Polymorphism**: Services can be extended or replaced

### Adding New Features

1. **New Data Source**: Extend `CompanySearchService` with new API
2. **New Export Format**: Add method to `JobSeekerApp.export_results()`
3. **New Location Method**: Add method to `LocationService`

## License 📝

This project is for educational purposes. Please respect:
- LinkedIn's Terms of Service
- OpenStreetMap's Usage Policy
- Rate limits of all APIs used

## Support 💬

For issues or questions:
1. Check the logs in `logs/jobseeker.log`
2. Review the configuration in `.env`
3. Ensure all dependencies are installed

## Future Enhancements 🚀

- [ ] GUI interface using Tkinter or PyQt
- [ ] Database storage for results
- [ ] Email notifications
- [ ] Job posting scraping
- [ ] Resume matching
- [ ] Application tracking

---

**Happy Job Hunting! 🎯**
