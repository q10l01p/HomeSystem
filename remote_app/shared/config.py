"""
Common configuration management for remote services.
"""
import os
from typing import Optional

class Config:
    """Base configuration class for remote services."""
    
    # Common settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'service.log')
    
    # Request limits
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '100')) * 1024 * 1024  # Default 100MB
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '300'))  # Default 5 minutes
    
    @classmethod
    def get_str(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get string environment variable."""
        return os.getenv(key, default)
    
    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        """Get integer environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')


class OCRServiceConfig(Config):
    """Configuration specific to OCR service."""
    
    # Service configuration - OCR service specific port with fallback  
    PORT = int(os.getenv('OCR_SERVICE_PORT', os.getenv('PORT', '5001')))
    
    # OCR specific settings
    MAX_PAGES = int(os.getenv('OCR_MAX_PAGES', '50'))
    TEMP_DIR = os.getenv('OCR_TEMP_DIR', '/tmp/ocr_service')
    RESULTS_DIR = os.getenv('OCR_RESULTS_DIR', '/tmp/ocr_results')
    
    # MinerU API settings
    MINERU_API_KEY = os.getenv('MINERU_API_KEY', '')
    MINERU_BASE_URL = os.getenv('MINERU_BASE_URL', 'https://mineru.net')
    MINERU_TIMEOUT = int(os.getenv('MINERU_TIMEOUT', '600'))  # 10 minutes
    MINERU_POLL_INTERVAL = int(os.getenv('MINERU_POLL_INTERVAL', '5'))  # 5 seconds