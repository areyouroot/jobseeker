"""
Company Search Service Module
==============================

This module provides company search functionality based on location and distance.
It uses OpenStreetMap's Overpass API to find companies within a specified radius.

Features:
- Search companies by location and radius
- Filter by business type/category
- Sort results by distance
- Cache results to minimize API calls

Author: Job Seeker Team
Date: 2026-02-15
"""

import logging
import requests
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from location_service import Location
from config import config
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class Company:
    """
    Data class representing a company/business.
    
    Attributes:
        name (str): Company name
        location (Location): Company location
        category (str): Business category/type
        address (str): Full address
        phone (Optional[str]): Phone number if available
        website (Optional[str]): Website URL if available
        distance_km (float): Distance from search origin in kilometers
        additional_info (Dict): Additional metadata
    """
    name: str
    location: Location
    category: str
    address: str
    phone: Optional[str] = None
    website: Optional[str] = None
    distance_km: float = 0.0
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of company."""
        return f"{self.name} ({self.category}) - {self.distance_km:.2f}km away"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert company to dictionary format.
        
        Returns:
            Dict[str, Any]: Company data as dictionary
        """
        return {
            'name': self.name,
            'category': self.category,
            'address': self.address,
            'phone': self.phone,
            'website': self.website,
            'distance_km': round(self.distance_km, 2),
            'latitude': self.location.latitude,
            'longitude': self.location.longitude,
        }


class CompanySearchService:
    """
    Service class for searching companies based on location and distance.
    
    This class provides methods to:
    - Search for companies within a radius
    - Filter companies by category
    - Sort results by distance or relevance
    - Cache search results
    
    Attributes:
        logger (Logger): Logger instance
        cache (Dict): Cache for search results
        cache_duration (timedelta): How long to cache results
    """
    
    # Rate limit: 1 request per second to be respectful to free API
    RATE_LIMIT_CALLS = 1
    RATE_LIMIT_PERIOD = 1  # seconds
    
    def __init__(self):
        """
        Initialize the CompanySearchService.
        
        Sets up logging, caching, and API configuration.
        """
        self.logger = logging.getLogger('JobSeeker.CompanySearchService')
        
        # Cache to store search results
        self.cache: Dict[str, tuple] = {}
        self.cache_duration = timedelta(hours=24)
        
        # Overpass API endpoint (OpenStreetMap)
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        
        self.logger.info("CompanySearchService initialized")
    
    @sleep_and_retry
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _make_api_request(self, query: str) -> Optional[Dict]:
        """
        Make a rate-limited API request to Overpass API.
        
        This method includes:
        - Rate limiting to respect API usage policies
        - Retry logic with exponential backoff
        - Error handling
        
        Args:
            query (str): Overpass QL query
            
        Returns:
            Optional[Dict]: API response data or None if request fails
        """
        try:
            self.logger.debug(f"Making Overpass API request...")
            
            response = requests.post(
                self.overpass_url,
                data={'data': query},
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return None
    
    def search_companies(
        self,
        origin: Location,
        radius_km: float,
        categories: Optional[List[str]] = None
    ) -> List[Company]:
        """
        Search for companies within a specified radius from origin location.
        
        This method queries OpenStreetMap's Overpass API to find businesses
        within the specified radius. Results are cached for 24 hours.
        
        Args:
            origin (Location): Center point for search
            radius_km (float): Search radius in kilometers
            categories (Optional[List[str]]): Filter by business categories
                Examples: ['office', 'shop', 'company', 'industrial']
                If None, searches all business types
                
        Returns:
            List[Company]: List of companies found, sorted by distance
            
        Example:
            >>> service = CompanySearchService()
            >>> location = Location(25.2048, 55.2708, "Dubai, UAE")
            >>> companies = service.search_companies(location, 10.0)
            >>> print(f"Found {len(companies)} companies")
        """
        # Check cache first
        cache_key = f"{origin.latitude},{origin.longitude},{radius_km}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                self.logger.info(f"Returning cached results for {cache_key}")
                return cached_data
        
        self.logger.info(
            f"Searching for companies within {radius_km}km of "
            f"({origin.latitude}, {origin.longitude})"
        )
        
        # Convert km to meters for Overpass API
        radius_m = int(radius_km * 1000)
        
        # Build Overpass QL query
        # This searches for nodes and ways tagged as offices
        query = f"""
        [out:json][timeout:60];
        (
          node["office"](around:{radius_m},{origin.latitude},{origin.longitude});
          way["office"](around:{radius_m},{origin.latitude},{origin.longitude});
        );
        out body;
        >;
        out skel qt;
        """
        
        # Make API request
        data = self._make_api_request(query)
        
        if not data or 'elements' not in data:
            self.logger.warning("No data returned from API")
            return []
        
        # Parse results
        companies = []
        seen_names = set()  # Avoid duplicates
        
        for element in data['elements']:
            # Skip if no tags
            if 'tags' not in element:
                continue
            
            tags = element['tags']
            
            # Extract company name
            name = tags.get('name') or tags.get('brand') or tags.get('operator')
            if not name or name in seen_names:
                continue
            
            seen_names.add(name)
            
            # Get coordinates
            if 'lat' in element and 'lon' in element:
                lat, lon = element['lat'], element['lon']
            elif 'center' in element:
                lat, lon = element['center']['lat'], element['center']['lon']
            else:
                continue
            
            # Create location object
            company_location = Location(
                latitude=lat,
                longitude=lon,
                address=tags.get('addr:full') or tags.get('addr:street', 'N/A'),
                city=tags.get('addr:city'),
                country=tags.get('addr:country')
            )
            
            # Calculate distance
            distance = origin.distance_to(company_location)
            
            # Determine category
            category = (
                tags.get('office') or 
                tags.get('shop') or 
                tags.get('amenity') or 
                'business'
            )
            
            # Create company object
            company = Company(
                name=name,
                location=company_location,
                category=category,
                address=company_location.address,
                phone=tags.get('phone'),
                website=tags.get('website'),
                distance_km=distance,
                additional_info={
                    'opening_hours': tags.get('opening_hours'),
                    'email': tags.get('email'),
                }
            )
            
            companies.append(company)
        
        # Sort by distance
        companies.sort(key=lambda c: c.distance_km)
        
        # Cache results
        self.cache[cache_key] = (companies, datetime.now())
        
        self.logger.info(f"Found {len(companies)} companies")
        return companies
    
    def filter_by_category(
        self,
        companies: List[Company],
        categories: List[str]
    ) -> List[Company]:
        """
        Filter companies by category.
        
        Args:
            companies (List[Company]): List of companies to filter
            categories (List[str]): Categories to include
            
        Returns:
            List[Company]: Filtered list of companies
        """
        return [
            c for c in companies 
            if any(cat.lower() in c.category.lower() for cat in categories)
        ]
    
    def get_top_companies(
        self,
        companies: List[Company],
        limit: int = 10
    ) -> List[Company]:
        """
        Get top N closest companies.
        
        Args:
            companies (List[Company]): List of companies
            limit (int): Maximum number of companies to return
            
        Returns:
            List[Company]: Top N companies by distance
        """
        return companies[:limit]
