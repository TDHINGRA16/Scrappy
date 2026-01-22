"""
Deduplication Service for Scrappy v2.0

Manages deduplication using Place ID (primary), CID (secondary), and href (fallback).
Based on best practices from OutScraper and Apify.

Place ID: 0x890cb024fe77e7b6 - Extracted from Google Maps URL
CID: Customer ID - Hex to decimal conversion from Feature ID
"""

import re
import logging
from typing import Optional, Set, Dict, Any

logger = logging.getLogger(__name__)


class PlaceIDDeduplicationService:
    """
    Manages deduplication using Place ID, CID, and href.
    
    Priority order for deduplication:
    1. Place ID (0x... format) - Most reliable, 100% unique per business
    2. CID (Customer ID) - Decimal conversion from hex
    3. Href (full URL) - Last resort fallback
    
    Example Place IDs:
    - 0x890cb024fe77e7b6
    - 0x89c3afa1b597fe49
    
    Example URLs:
    - /maps/place/Pizza+Hut/...!3m4!1s0x890cb024fe77e7b6!...
    """
    
    # Regex pattern to extract Place ID from URL
    # Matches: 0x followed by hexadecimal characters
    PLACE_ID_PATTERN = re.compile(r'0x[a-f0-9]+', re.IGNORECASE)
    
    # Pattern to extract from full Google Maps URL structure
    # The Place ID typically appears after "1s" in the URL
    PLACE_ID_URL_PATTERN = re.compile(r'!1s(0x[a-f0-9]+:[a-f0-9x]+)', re.IGNORECASE)
    
    # Pattern for Feature ID (contains both hex values separated by colon)
    FEATURE_ID_PATTERN = re.compile(r'(0x[a-f0-9]+):(0x[a-f0-9]+)', re.IGNORECASE)
    
    def __init__(self):
        """Initialize the deduplication service with empty sets"""
        self.seen_place_ids: Set[str] = set()
        self.seen_cids: Set[str] = set()
        self.seen_hrefs: Set[str] = set()
        self.seen_names_addresses: Set[str] = set()  # Additional fallback
        
        # Statistics
        self.dedup_stats = {
            'total_checked': 0,
            'duplicates_removed': 0,
            'unique_kept': 0,
            'by_place_id': 0,
            'by_cid': 0,
            'by_href': 0,
            'by_name_address': 0
        }
    
    @staticmethod
    def extract_place_id(href: str) -> Optional[str]:
        """
        Extract Place ID from Google Maps URL.
        
        Args:
            href: Google Maps URL containing place information
            
        Returns:
            Place ID in format "0x..." or None if not found
            
        Examples:
            Input: "/maps/place/Pizza+Hut/...!1s0x890cb024fe77e7b6:0x123..."
            Output: "0x890cb024fe77e7b6"
        """
        if not href:
            return None
            
        try:
            # First try to find the full feature ID pattern
            feature_match = PlaceIDDeduplicationService.FEATURE_ID_PATTERN.search(href)
            if feature_match:
                # Return the first hex part (the actual Place ID)
                return feature_match.group(1).lower()
            
            # Fallback: Find any hex pattern starting with 0x
            matches = PlaceIDDeduplicationService.PLACE_ID_PATTERN.findall(href)
            if matches:
                # Return the longest match (most likely to be complete)
                return max(matches, key=len).lower()
                
        except Exception as e:
            logger.warning(f"Error extracting Place ID from href: {e}")
            
        return None
    
    @staticmethod
    def extract_cid_from_feature_id(feature_id: str) -> Optional[str]:
        """
        Extract CID (Customer ID) from Feature ID by converting hex to decimal.
        
        Args:
            feature_id: Feature ID in format "0x...:0x..."
            
        Returns:
            CID as decimal string or None if not found
            
        Example:
            Input: "0x89c3afa1b597fe49:0x890cb024fe77e7b6"
            Return: "9876543210987654321" (decimal of second hex)
        """
        if not feature_id:
            return None
            
        try:
            # Extract both hex parts from feature ID
            match = PlaceIDDeduplicationService.FEATURE_ID_PATTERN.search(feature_id)
            if match:
                # The second hex value is typically the CID
                hex_value = match.group(2)
                # Convert hex to decimal
                cid = str(int(hex_value, 16))
                return cid
                
            # If no colon, try direct conversion
            hex_match = PlaceIDDeduplicationService.PLACE_ID_PATTERN.search(feature_id)
            if hex_match:
                cid = str(int(hex_match.group(), 16))
                return cid
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error extracting CID from feature ID: {e}")
            
        return None
    
    @staticmethod
    def extract_cid_from_url(url: str) -> Optional[str]:
        """
        Extract CID directly from Google Maps URL if present.
        
        Args:
            url: Full Google Maps URL
            
        Returns:
            CID as string or None
        """
        if not url:
            return None
            
        try:
            # CID sometimes appears in URL as "cid=123..."
            cid_match = re.search(r'cid=(\d+)', url)
            if cid_match:
                return cid_match.group(1)
                
            # Or extract from data attribute patterns
            data_match = re.search(r'data=.*?(\d{15,20})', url)
            if data_match:
                return data_match.group(1)
                
        except Exception as e:
            logger.warning(f"Error extracting CID from URL: {e}")
            
        return None
    
    def is_duplicate(
        self,
        place_id: Optional[str] = None,
        cid: Optional[str] = None,
        href: Optional[str] = None,
        name: Optional[str] = None,
        address: Optional[str] = None
    ) -> bool:
        """
        Check if a place is a duplicate based on identifiers.
        
        Priority order:
        1. Place ID - Most reliable
        2. CID - Secondary identifier
        3. Href - URL-based dedup
        4. Name + Address combo - Last resort
        
        Args:
            place_id: Primary unique identifier
            cid: Customer ID (secondary)
            href: Full URL to the place
            name: Business name (fallback)
            address: Business address (fallback)
            
        Returns:
            True if duplicate, False if unique
        """
        self.dedup_stats['total_checked'] += 1
        
        # Check Place ID first (primary)
        if place_id:
            place_id_lower = place_id.lower()
            if place_id_lower in self.seen_place_ids:
                self.dedup_stats['duplicates_removed'] += 1
                logger.debug(f"Duplicate found by Place ID: {place_id}")
                return True
        
        # Check CID (secondary)
        if cid:
            if cid in self.seen_cids:
                self.dedup_stats['duplicates_removed'] += 1
                logger.debug(f"Duplicate found by CID: {cid}")
                return True
        
        # Check href (fallback)
        if href:
            # Normalize href for comparison
            href_normalized = href.split('?')[0].lower()
            if href_normalized in self.seen_hrefs:
                self.dedup_stats['duplicates_removed'] += 1
                logger.debug(f"Duplicate found by href")
                return True
        
        # Check name + address combo (last resort)
        if name and address:
            name_addr_key = f"{name.lower().strip()}|{address.lower().strip()}"
            if name_addr_key in self.seen_names_addresses:
                self.dedup_stats['duplicates_removed'] += 1
                logger.debug(f"Duplicate found by name+address: {name}")
                return True
        
        # Not a duplicate
        return False
    
    def add_place(
        self,
        place_id: Optional[str] = None,
        cid: Optional[str] = None,
        href: Optional[str] = None,
        name: Optional[str] = None,
        address: Optional[str] = None
    ) -> bool:
        """
        Add a place to the seen sets for future deduplication.
        
        Args:
            place_id: Primary unique identifier
            cid: Customer ID (secondary)
            href: Full URL to the place
            name: Business name (fallback)
            address: Business address (fallback)
            
        Returns:
            True if added (was unique), False if was duplicate
        """
        # Check for duplicate first
        if self.is_duplicate(place_id, cid, href, name, address):
            return False
        
        # Add to appropriate sets
        if place_id:
            self.seen_place_ids.add(place_id.lower())
            self.dedup_stats['by_place_id'] += 1
        
        if cid:
            self.seen_cids.add(cid)
            self.dedup_stats['by_cid'] += 1
        
        if href:
            href_normalized = href.split('?')[0].lower()
            self.seen_hrefs.add(href_normalized)
            self.dedup_stats['by_href'] += 1
        
        if name and address:
            name_addr_key = f"{name.lower().strip()}|{address.lower().strip()}"
            self.seen_names_addresses.add(name_addr_key)
            self.dedup_stats['by_name_address'] += 1
        
        self.dedup_stats['unique_kept'] += 1
        return True
    
    def process_result(self, result: Dict[str, Any]) -> bool:
        """
        Process a scraping result and add to dedup if unique.
        
        Args:
            result: Dictionary containing scraped business data
            
        Returns:
            True if unique and added, False if duplicate
        """
        return self.add_place(
            place_id=result.get('place_id'),
            cid=result.get('cid'),
            href=result.get('href'),
            name=result.get('name'),
            address=result.get('address')
        )
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get deduplication statistics.
        
        Returns:
            Dictionary with dedup statistics
        """
        stats = {
            **self.dedup_stats,
            'total_place_ids': len(self.seen_place_ids),
            'total_cids': len(self.seen_cids),
            'total_hrefs': len(self.seen_hrefs),
            'dedup_rate': (
                self.dedup_stats['duplicates_removed'] / self.dedup_stats['total_checked'] * 100
                if self.dedup_stats['total_checked'] > 0 else 0
            )
        }
        
        # Log stats summary
        if self.dedup_stats['total_checked'] > 0:
            logger.info(
                f"📊 Dedup Stats: {stats['unique_kept']} unique / "
                f"{self.dedup_stats['total_checked']} checked | "
                f"Removed: {self.dedup_stats['duplicates_removed']} ({stats['dedup_rate']:.1f}%)"
            )
        
        return stats
    
    def reset(self) -> None:
        """Reset all seen sets and statistics"""
        self.seen_place_ids.clear()
        self.seen_cids.clear()
        self.seen_hrefs.clear()
        self.seen_names_addresses.clear()
        self.dedup_stats = {
            'total_checked': 0,
            'duplicates_removed': 0,
            'unique_kept': 0,
            'by_place_id': 0,
            'by_cid': 0,
            'by_href': 0,
            'by_name_address': 0
        }
        logger.info("Deduplication service reset")
    
    def __len__(self) -> int:
        """Return count of unique places tracked"""
        return len(self.seen_place_ids) + len(self.seen_cids)
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"PlaceIDDeduplicationService("
            f"place_ids={len(self.seen_place_ids)}, "
            f"cids={len(self.seen_cids)}, "
            f"hrefs={len(self.seen_hrefs)})"
        )


# Global instance for shared use
dedup_service = PlaceIDDeduplicationService()
