"""
Helper utilities for Scrappy v2.0

Common utility functions used across the application.
"""

import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


def clean_phone_number(phone: str) -> Optional[str]:
    """
    Clean and normalize a phone number.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        Cleaned phone number or None if invalid
        
    Examples:
        "+91 987-654-3210" -> "+919876543210"
        "(987) 654-3210" -> "9876543210"
    """
    if not phone:
        return None
    
    # Remove common prefixes that aren't part of the number
    prefixes_to_remove = ['Phone:', 'Tel:', 'Mobile:', 'Call:']
    for prefix in prefixes_to_remove:
        phone = phone.replace(prefix, '').strip()
    
    # Keep only digits and +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Validate length (should be 10-15 digits)
    digits_only = re.sub(r'\D', '', cleaned)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return None
    
    return cleaned


def clean_address(address: str) -> Optional[str]:
    """
    Clean an address string.
    
    Args:
        address: Raw address string
        
    Returns:
        Cleaned address or None
    """
    if not address:
        return None
    
    # Remove common prefixes
    prefixes_to_remove = ['Address:', 'Located at:', 'Find us at:']
    for prefix in prefixes_to_remove:
        address = address.replace(prefix, '').strip()
    
    # Remove excessive whitespace
    address = ' '.join(address.split())
    
    return address if address else None


def clean_website(url: str) -> Optional[str]:
    """
    Clean and validate a website URL.
    
    Args:
        url: Raw URL string
        
    Returns:
        Cleaned URL or None
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Skip Google redirect URLs
    if 'google.com' in url and '/url?' in url:
        # Try to extract the actual URL
        match = re.search(r'url=([^&]+)', url)
        if match:
            url = match.group(1)
    
    # Add protocol if missing
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url


def parse_rating(rating_text: str) -> Optional[float]:
    """
    Parse rating from text.
    
    Args:
        rating_text: Text containing rating (e.g., "4.5 stars")
        
    Returns:
        Rating as float or None
    """
    if not rating_text:
        return None
    
    try:
        # Look for number pattern
        match = re.search(r'(\d+\.?\d*)', rating_text)
        if match:
            rating = float(match.group(1))
            # Validate rating is in expected range
            if 0 <= rating <= 5:
                return rating
    except (ValueError, AttributeError):
        pass
    
    return None


def parse_reviews_count(reviews_text: str) -> Optional[int]:
    """
    Parse reviews count from text.
    
    Args:
        reviews_text: Text containing reviews count (e.g., "342 reviews")
        
    Returns:
        Reviews count as integer or None
    """
    if not reviews_text:
        return None
    
    try:
        # Remove commas and find number
        text = reviews_text.replace(',', '')
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
    except (ValueError, AttributeError):
        pass
    
    return None


def extract_coordinates_from_url(url: str) -> Optional[Dict[str, float]]:
    """
    Extract latitude and longitude from Google Maps URL.
    
    Args:
        url: Google Maps URL
        
    Returns:
        Dictionary with 'latitude' and 'longitude' or None
        
    Example URL patterns:
        - @31.6340,74.8723,15z
        - !3d31.6340!4d74.8723
    """
    if not url:
        return None
    
    try:
        # Pattern 1: @lat,lng,zoom
        match = re.search(r'@(-?\d+\.?\d*),(-?\d+\.?\d*)', url)
        if match:
            return {
                'latitude': float(match.group(1)),
                'longitude': float(match.group(2))
            }
        
        # Pattern 2: !3dlat!4dlng
        match = re.search(r'!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)', url)
        if match:
            return {
                'latitude': float(match.group(1)),
                'longitude': float(match.group(2))
            }
            
    except (ValueError, AttributeError):
        pass
    
    return None


def format_business_for_display(business: Dict[str, Any]) -> str:
    """
    Format a business dictionary for display/logging.
    
    Args:
        business: Business data dictionary
        
    Returns:
        Formatted string representation
    """
    name = business.get('name', 'Unknown')
    rating = business.get('rating', 'N/A')
    reviews = business.get('reviews_count', 0)
    phone = business.get('phone', 'N/A')
    
    return f"{name} | ⭐ {rating} ({reviews} reviews) | 📞 {phone}"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get_nested(data: Dict, *keys, default=None) -> Any:
    """
    Safely get a nested value from a dictionary.
    
    Args:
        data: Source dictionary
        *keys: Keys to traverse
        default: Default value if key not found
        
    Returns:
        Value at the nested key or default
        
    Example:
        safe_get_nested({'a': {'b': 1}}, 'a', 'b') -> 1
        safe_get_nested({'a': {}}, 'a', 'b', 'c', default=0) -> 0
    """
    current = data
    for key in keys:
        try:
            current = current[key]
        except (KeyError, TypeError, IndexError):
            return default
    return current


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if not s or len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def generate_timestamp() -> str:
    """Generate ISO format timestamp"""
    return datetime.utcnow().isoformat() + "Z"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string for use as a filename.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Limit length
    return sanitized[:100]


def results_to_csv_rows(results: List[Dict[str, Any]]) -> List[List[str]]:
    """
    Convert business results to CSV rows.
    
    Args:
        results: List of business dictionaries
        
    Returns:
        List of rows (each row is a list of values)
    """
    headers = [
        'Place ID', 'Name', 'Address', 'Phone', 'Website',
        'Rating', 'Reviews', 'Category', 'Hours', 'Is Claimed'
    ]
    
    rows = [headers]
    
    for r in results:
        row = [
            r.get('place_id', ''),
            r.get('name', ''),
            r.get('address', ''),
            r.get('phone', ''),
            r.get('website', ''),
            str(r.get('rating', '')),
            str(r.get('reviews_count', '')),
            r.get('category', ''),
            r.get('hours', ''),
            'Yes' if r.get('is_claimed') else 'No'
        ]
        rows.append(row)
    
    return rows


def merge_business_data(
    existing: Dict[str, Any],
    new: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge two business data dictionaries, preferring non-empty values.
    
    Args:
        existing: Existing business data
        new: New business data to merge
        
    Returns:
        Merged dictionary
    """
    merged = existing.copy()
    
    for key, value in new.items():
        # Only update if new value is non-empty and existing is empty
        if value and not merged.get(key):
            merged[key] = value
    
    return merged


class Timer:
    """Context manager for timing code blocks"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"{self.name} completed in {self.duration:.2f} seconds")
    
    def elapsed(self) -> float:
        """Get elapsed time in seconds"""
        if self.duration:
            return self.duration
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0
