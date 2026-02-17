"""
Location Service Module
=======================

This module provides location detection and geocoding services.
It supports multiple methods for determining user location:
- IP-based geolocation (free, no API key required)
- Google Maps Geocoding API (more accurate, requires API key)
- Manual coordinate input

Author: Job Seeker Team
Date: 2026-02-15
"""

import logging
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
import geocoder
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from config import config


@dataclass
class Location:
    """
    Data class representing a geographic location.
    
    Attributes:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        address (str): Human-readable address
        city (str): City name
        country (str): Country name
    """
    latitude: float
    longitude: float
    address: str
    city: Optional[str] = None
    country: Optional[str] = None
    
    @property
    def coordinates(self) -> Tuple[float, float]:
        """
        Get coordinates as a tuple.
        
        Returns:
            Tuple[float, float]: (latitude, longitude)
        """
        return (self.latitude, self.longitude)
    
    def distance_to(self, other: 'Location') -> float:
        """
        Calculate distance to another location in kilometers.
        
        Args:
            other (Location): Target location
            
        Returns:
            float: Distance in kilometers
        """
        return geodesic(self.coordinates, other.coordinates).kilometers
    
    def __str__(self) -> str:
        """String representation of location."""
        return f"{self.address} ({self.latitude:.4f}, {self.longitude:.4f})"


class LocationService:
    """
    Service class for location detection and geocoding operations.
    
    This class provides methods to:
    - Detect current location using IP geolocation
    - Geocode addresses to coordinates
    - Reverse geocode coordinates to addresses
    - Calculate distances between locations
    
    Attributes:
        logger (Logger): Logger instance for this service
        geolocator (Nominatim): Geocoding service instance
    """
    
    def __init__(self):
        """
        Initialize the LocationService.
        
        Sets up logging and geocoding service with appropriate user agent.
        """
        self.logger = logging.getLogger('JobSeeker.LocationService')
        
        # Initialize geocoding service with user agent
        # User agent is required by Nominatim's usage policy
        self.geolocator = Nominatim(user_agent="jobseeker_app_v1.0")
        
        self.logger.info("LocationService initialized")
    
    def get_current_location(self) -> Optional[Location]:
        """
        Detect current location using IP-based geolocation.
        
        This method uses the user's IP address to determine their
        approximate location. It's free but less accurate than GPS.
        
        Returns:
            Optional[Location]: Current location or None if detection fails
            
        Example:
            >>> service = LocationService()
            >>> location = service.get_current_location()
            >>> print(f"You are in {location.city}")
        """
        try:
            self.logger.info("Detecting current location via IP...")
            
            # Use IP-based geolocation (free service)
            g = geocoder.ip('me')
            
            if g.ok:
                location = Location(
                    latitude=g.latlng[0],
                    longitude=g.latlng[1],
                    address=g.address,
                    city=g.city,
                    country=g.country
                )
                
                self.logger.info(f"Location detected: {location}")
                return location
            else:
                self.logger.error("Failed to detect location via IP")
                return None
                
        except Exception as e:
            self.logger.error(f"Error detecting location: {e}")
            return None
    
    def geocode_address(self, address: str) -> Optional[Location]:
        """
        Convert an address string to geographic coordinates.
        
        Args:
            address (str): Address to geocode (e.g., "Dubai, UAE")
            
        Returns:
            Optional[Location]: Location object or None if geocoding fails
            
        Example:
            >>> service = LocationService()
            >>> location = service.geocode_address("Chennai, India")
            >>> print(location.coordinates)
        """
        try:
            self.logger.info(f"Geocoding address: {address}")
            
            # Use Nominatim for free geocoding
            location_data = self.geolocator.geocode(address)
            
            if location_data:
                # Extract city and country from address components
                address_parts = location_data.address.split(', ')
                
                location = Location(
                    latitude=location_data.latitude,
                    longitude=location_data.longitude,
                    address=location_data.address,
                    city=address_parts[0] if len(address_parts) > 0 else None,
                    country=address_parts[-1] if len(address_parts) > 0 else None
                )
                
                self.logger.info(f"Geocoded successfully: {location}")
                return location
            else:
                self.logger.warning(f"Could not geocode address: {address}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error geocoding address: {e}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Location]:
        """
        Convert coordinates to a human-readable address.
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            
        Returns:
            Optional[Location]: Location object or None if reverse geocoding fails
            
        Example:
            >>> service = LocationService()
            >>> location = service.reverse_geocode(25.2048, 55.2708)
            >>> print(location.address)
        """
        try:
            self.logger.info(f"Reverse geocoding: ({latitude}, {longitude})")
            
            # Reverse geocode using Nominatim
            location_data = self.geolocator.reverse(f"{latitude}, {longitude}")
            
            if location_data:
                address_parts = location_data.address.split(', ')
                
                location = Location(
                    latitude=latitude,
                    longitude=longitude,
                    address=location_data.address,
                    city=address_parts[0] if len(address_parts) > 0 else None,
                    country=address_parts[-1] if len(address_parts) > 0 else None
                )
                
                self.logger.info(f"Reverse geocoded successfully: {location}")
                return location
            else:
                self.logger.warning(f"Could not reverse geocode coordinates")
                return None
                
        except Exception as e:
            self.logger.error(f"Error reverse geocoding: {e}")
            return None
    
    def get_location_interactive(self) -> Optional[Location]:
        """
        Get location through interactive user input.
        
        Prompts the user to either:
        1. Use automatic IP-based detection
        2. Enter a city/address manually
        3. Enter coordinates manually
        
        Returns:
            Optional[Location]: User's location or None if input fails
        """
        print("\n=== Location Detection ===")
        print("1. Auto-detect using IP address (recommended)")
        print("2. Enter city/address manually")
        print("3. Enter coordinates manually")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            return self.get_current_location()
            
        elif choice == '2':
            address = input("Enter city or address: ").strip()
            if address:
                return self.geocode_address(address)
            else:
                self.logger.warning("No address provided")
                return None
                
        elif choice == '3':
            try:
                lat = float(input("Enter latitude: ").strip())
                lon = float(input("Enter longitude: ").strip())
                return self.reverse_geocode(lat, lon)
            except ValueError:
                self.logger.error("Invalid coordinates provided")
                return None
        else:
            self.logger.warning("Invalid option selected")
            return None
