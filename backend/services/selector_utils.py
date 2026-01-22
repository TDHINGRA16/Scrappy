"""
Selector Utility Functions for Google Maps Scraping

Google Maps frequently changes CSS class names and DOM structure.
This module provides robust selector chains with fallback strategies.

Usage:
    from services.selector_utils import SelectorChain
    
    name = await SelectorChain.get_text(
        page,
        selectors=["h1.DUwDvf.lfPIob", "h1.fontHeadlineLarge", "h1"]
    )
"""

import re
import logging
from typing import List, Optional, Dict, Any
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class SelectorChain:
    """
    Try multiple selectors until one works.
    Essential for scraping Google Maps which changes selectors frequently.
    """
    
    @staticmethod
    async def get_text(
        page: Page,
        selectors: List[str],
        fallback: Optional[str] = None
    ) -> Optional[str]:
        """
        Try each selector until text is found.
        
        Args:
            page: Playwright page object
            selectors: List of CSS selectors to try in order
            fallback: Default value if no selector works
            
        Returns:
            Text content from first matching selector, or fallback
        """
        for selector in selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    # Try inner_text first (visible text only)
                    text = await element.inner_text()
                    if text and text.strip():
                        return text.strip()
                    # Fallback to text_content (includes hidden text)
                    text = await element.text_content()
                    if text and text.strip():
                        return text.strip()
            except Exception as e:
                logger.debug(f"Selector failed '{selector}': {e}")
                continue
        
        return fallback
    
    @staticmethod
    async def get_attribute(
        page: Page,
        selectors: List[str],
        attribute: str,
        fallback: Optional[str] = None
    ) -> Optional[str]:
        """
        Try each selector until attribute is found.
        
        Args:
            page: Playwright page object
            selectors: List of CSS selectors to try in order
            attribute: HTML attribute to extract (e.g., 'href', 'aria-label')
            fallback: Default value if no selector works
            
        Returns:
            Attribute value from first matching selector, or fallback
        """
        for selector in selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    attr = await element.get_attribute(attribute)
                    if attr:
                        return attr.strip()
            except Exception as e:
                logger.debug(f"Selector failed '{selector}' for attribute '{attribute}': {e}")
                continue
        
        return fallback
    
    @staticmethod
    async def extract_from_aria_label(
        page: Page,
        selector: str,
        pattern: str,
        group: int = 1
    ) -> Optional[str]:
        """
        Extract text from aria-label using regex pattern.
        
        Args:
            page: Playwright page object
            selector: CSS selector for element with aria-label
            pattern: Regex pattern to extract from aria-label
            group: Regex group number to return
            
        Returns:
            Matched text or None
        """
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                aria_label = await element.get_attribute("aria-label")
                if aria_label:
                    match = re.search(pattern, aria_label)
                    if match:
                        return match.group(group).strip()
        except Exception as e:
            logger.debug(f"Failed to extract from aria-label '{selector}': {e}")
        
        return None


# Updated Google Maps selectors (January 2026)
# These may need updating if Google changes their HTML structure again
GOOGLE_MAPS_SELECTORS = {
    "name": [
        "h1.DUwDvf.lfPIob",          # Primary selector (2026)
        "h1.fontHeadlineLarge",       # Fallback 1
        "div.lMbq3e h1",              # Fallback 2
        "h1[class*='fontHeadline']",  # Pattern match
        "h1",                         # Last resort
    ],
    "rating": [
        "div.F7nice span[aria-hidden='true']",  # Primary 2026
        "span.ceNzKf[role='img']",              # Alternative
        "div[role='img'][aria-label*='star']",  # Legacy
    ],
    "reviews_button": [
        "div.F7nice button[aria-label*='reviews']",  # Primary 2026
        "button[aria-label*='review']",              # Fallback
        "span[aria-label*='review']",                # Alternative
    ],
    "category": [
        "button.DkEaL",                   # Primary 2026
        "span.DkEaL",                     # Alternative
        "button[jsaction*='category']",   # Legacy
    ],
    "address": [
        "button[data-item-id='address']",
        "button[data-item-id*='address']",
        "button[aria-label*='Address']",
    ],
    "phone": [
        "button[data-item-id*='phone']",
        "button[aria-label*='Phone']",
    ],
    "website": [
        "a[data-item-id='authority']",
        "a[aria-label*='Website']",
    ],
    "hours": [
        "button[data-item-id*='oh']",
        "div[aria-label*='hour']",
        "button[aria-label*='Hours']",
    ],
}


async def extract_business_details_v2(page: Page, card_url: str) -> Optional[Dict[str, Any]]:
    """
    Extract business details using the latest selectors (Jan 2026).
    
    This is an alternative extraction method with updated selectors.
    Use this if the main scraper extraction is failing.
    
    Args:
        page: Playwright page with loaded business detail page
        card_url: URL of the business (for Place ID extraction)
        
    Returns:
        Dictionary with business details, or None if name extraction fails
    """
    try:
        # Business Name - Critical field
        name = await SelectorChain.get_text(page, GOOGLE_MAPS_SELECTORS["name"])
        
        if not name or not name.strip() or name.lower() == 'none':
            logger.warning(f"⚠️ Could not extract name from {card_url[:60]}...")
            return None
        
        # Rating
        rating = None
        for selector in GOOGLE_MAPS_SELECTORS["rating"]:
            try:
                el = page.locator(selector).first
                if await el.count() > 0:
                    if "aria-label" in selector:
                        aria = await el.get_attribute("aria-label")
                        if aria:
                            match = re.search(r'([\d.]+)\s*star', aria)
                            if match:
                                rating = float(match.group(1))
                                break
                    else:
                        text = await el.inner_text()
                        if text:
                            rating = float(text.replace(",", "."))
                            break
            except Exception:
                continue
        
        # Reviews count
        reviews_count = None
        for selector in GOOGLE_MAPS_SELECTORS["reviews_button"]:
            try:
                el = page.locator(selector).first
                if await el.count() > 0:
                    aria = await el.get_attribute("aria-label")
                    if aria:
                        match = re.search(r'([\d,]+)', aria)
                        if match:
                            reviews_count = int(match.group(1).replace(",", ""))
                            break
            except Exception:
                continue
        
        # Category
        category = await SelectorChain.get_text(page, GOOGLE_MAPS_SELECTORS["category"])
        
        # Phone
        phone = await SelectorChain.extract_from_aria_label(
            page, 
            GOOGLE_MAPS_SELECTORS["phone"][0],
            r'Phone:\s*(.+)'
        )
        
        # Website
        website = await SelectorChain.get_attribute(
            page,
            GOOGLE_MAPS_SELECTORS["website"],
            "href"
        )
        
        # Address
        address = await SelectorChain.extract_from_aria_label(
            page,
            GOOGLE_MAPS_SELECTORS["address"][0],
            r'Address:\s*(.+)'
        )
        
        # Hours
        hours = await SelectorChain.extract_from_aria_label(
            page,
            GOOGLE_MAPS_SELECTORS["hours"][0],
            r'Hours:\s*(.+)'
        )
        if not hours:
            hours = await SelectorChain.get_attribute(
                page,
                GOOGLE_MAPS_SELECTORS["hours"],
                "aria-label"
            )
        
        # Extract Place ID and CID from URL
        place_id = None
        cid = None
        try:
            place_match = re.search(r'!1s(0x[a-f0-9:]+)', card_url)
            if place_match:
                place_id = place_match.group(1)
            
            cid_match = re.search(r'!8m2!3d([\d.]+)!4d([\d.]+)', card_url)
            if cid_match:
                cid = f"{cid_match.group(1)}_{cid_match.group(2)}"
        except Exception:
            pass
        
        # Coordinates from URL
        latitude = None
        longitude = None
        try:
            coords_match = re.search(r'@(-?\d+\.?\d*),(-?\d+\.?\d*)', card_url)
            if coords_match:
                latitude = float(coords_match.group(1))
                longitude = float(coords_match.group(2))
        except Exception:
            pass
        
        result = {
            "place_id": place_id,
            "cid": cid,
            "name": name,
            "address": address,
            "phone": phone,
            "website": website,
            "rating": rating,
            "reviews_count": reviews_count,
            "category": category,
            "hours": hours,
            "latitude": latitude,
            "longitude": longitude,
            "is_claimed": None,
            "photo_url": None,
        }
        
        logger.info(f"✅ Extracted: {name} | ⭐ {rating} ({reviews_count} reviews)")
        return result
        
    except Exception as e:
        logger.error(f"❌ Extraction failed for {card_url[:60]}: {e}")
        return None
