"""
Configuration Module for Job Seeker Application
================================================

This module handles all configuration management including:
- Environment variable loading
- API key management
- Application settings
- Logging configuration

Author: Job Seeker Team
Date: 2026-02-15
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import colorlog


class Config:
    """
    Configuration class following Singleton pattern.
    
    This class manages all application configuration including API keys,
    settings, and logging. It ensures only one instance exists throughout
    the application lifecycle.
    
    Attributes:
        _instance (Config): Singleton instance
        google_maps_api_key (str): Google Maps API key
        linkedin_email (str): LinkedIn account email
        linkedin_password (str): LinkedIn account password
        max_linkedin_profiles (int): Maximum profiles to retrieve per company
        default_search_radius_km (int): Default search radius in kilometers
        rate_limit_rpm (int): Rate limit in requests per minute
        headless_browser (bool): Whether to run browser in headless mode
        log_level (str): Logging level
    """
    
    _instance: Optional['Config'] = None
    
    def __new__(cls) -> 'Config':
        """
        Implement Singleton pattern.
        
        Returns:
            Config: The single instance of Config class
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Initialize configuration by loading environment variables.
        
        This method loads the .env file and sets up all configuration
        parameters. It only runs once due to the Singleton pattern.
        """
        # Prevent re-initialization
        if self._initialized:
            return
            
        # Load environment variables from .env file
        env_path = Path(__file__).parent / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # API Keys
        self.google_maps_api_key: str = os.getenv('GOOGLE_MAPS_API_KEY', '')
        self.linkedin_email: str = os.getenv('LINKEDIN_EMAIL', '')
        self.linkedin_password: str = os.getenv('LINKEDIN_PASSWORD', '')
        
        # Application Settings
        self.max_linkedin_profiles: int = int(os.getenv('MAX_LINKEDIN_PROFILES', '5'))
        self.default_search_radius_km: int = int(os.getenv('DEFAULT_SEARCH_RADIUS_KM', '10'))
        self.rate_limit_rpm: int = int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', '10'))
        
        # Browser Settings
        headless_str = os.getenv('HEADLESS_BROWSER', 'True')
        self.headless_browser: bool = headless_str.lower() in ('true', '1', 'yes')
        
        # Logging Settings
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        
        # Setup logging
        self._setup_logging()
        
        # Mark as initialized
        self._initialized = True
        
        # Log configuration status
        self.logger.info("Configuration loaded successfully")
        if not self.google_maps_api_key:
            self.logger.warning("Google Maps API key not configured - using free alternatives")
    
    def _setup_logging(self) -> None:
        """
        Configure colored logging for the application.
        
        Sets up a colored console handler with timestamp, level, and message.
        The color scheme helps distinguish between different log levels.
        """
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Configure color scheme for different log levels
        log_colors = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
        
        # Create colored formatter
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors=log_colors
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Setup file handler (without colors)
        file_handler = logging.FileHandler(log_dir / 'jobseeker.log')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Configure root logger
        self.logger = logging.getLogger('JobSeeker')
        self.logger.setLevel(getattr(logging, self.log_level))
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def validate(self) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        is_valid = True
        
        # Check if at least one location service is available
        if not self.google_maps_api_key:
            self.logger.info("Will use free IP-based geolocation service")
        
        return is_valid
    
    def __repr__(self) -> str:
        """
        String representation of Config object.
        
        Returns:
            str: Configuration summary (without sensitive data)
        """
        return (
            f"Config(max_profiles={self.max_linkedin_profiles}, "
            f"radius={self.default_search_radius_km}km, "
            f"headless={self.headless_browser})"
        )


# Create global configuration instance
config = Config()
