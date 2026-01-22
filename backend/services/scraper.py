"""
Google Maps Scraper Service for Scrappy v2.0

Core scraping logic using Playwright with parallel card extraction.
Based on best practices from Apify, OutScraper, and SerpApi.

Key features:
- Single query, parallel card extraction (4-5 cards simultaneously)
- Smart scrolling with early termination
- Deduplication by Place ID
- Async/await with Semaphore for concurrency control
- Real-time progress tracking via progress_tracker
"""

import sys
import asyncio
import random
import re
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright

from config import settings, SELECTORS, GOOGLE_MAPS_SEARCH_URL, RATE_LIMIT
from services.deduplication import PlaceIDDeduplicationService

# Progress tracker import (optional - may not be used in sync mode)
try:
    from services.progress_tracker import update_scrape_progress
    PROGRESS_TRACKING_ENABLED = True
except ImportError:
    PROGRESS_TRACKING_ENABLED = False
    def update_scrape_progress(*args, **kwargs):
        pass  # No-op if tracker not available

# Fix for Windows: Set event loop policy before any Playwright operations
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass  # Already set

logger = logging.getLogger(__name__)


class GoogleMapsScraper:
    """
    Scrapes Google Maps cards in parallel.
    One query → 4-5 cards extracted simultaneously.
    
    Architecture:
    - Uses asyncio + Semaphore for lightweight concurrency
    - Each card extraction runs in separate browser context
    - Deduplication by Place ID (primary) and CID (secondary)
    - Optional progress tracking for async scrapes
    
    Why not threads?
    - Playwright discourages threading
    - Each thread = 50-150MB RAM
    - asyncio is lightweight and fast
    """
    
    def __init__(self, max_concurrent_cards: int = None):
        """
        Initialize the scraper.
        
        Args:
            max_concurrent_cards: Number of cards to extract simultaneously
                                 Recommended: 4-5 (150-200MB each)
        """
        self.max_concurrent_cards = max_concurrent_cards or settings.MAX_CONCURRENT_CARDS
        self.dedup_service = PlaceIDDeduplicationService()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        
        # Store search query for click-based extraction in parallel contexts
        self._current_search_query: Optional[str] = None
        self._current_search_url: Optional[str] = None
        
        # Progress tracking (set by routes for async scrapes)
        self._progress_scrape_id: Optional[str] = None
        
        # Statistics
        self.stats = {
            'cards_found': 0,
            'cards_extracted': 0,
            'extraction_errors': 0,
            'scrolls_performed': 0,
            'stale_scrolls': 0
        }
    
    def _update_progress(self, **kwargs):
        """Update progress if tracking is enabled"""
        if self._progress_scrape_id and PROGRESS_TRACKING_ENABLED:
            update_scrape_progress(self._progress_scrape_id, **kwargs)
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self) -> None:
        """Start Playwright and browser"""
        logger.info("Starting Playwright browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.HEADLESS,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-gpu',
                '--disable-software-rasterizer',
            ]
        )
        logger.info("Browser started successfully")
    
    async def close(self) -> None:
        """Close browser and Playwright"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
        if self.playwright:
            await self.playwright.stop()
            logger.info("Playwright stopped")
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the configured list"""
        return random.choice(settings.USER_AGENTS)
    
    async def _random_delay(self, min_sec: float, max_sec: float) -> None:
        """Wait for a random duration between min and max seconds"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    def _is_valid_business_name(self, name: Optional[str]) -> bool:
        """
        Check if a business name is valid (not a placeholder or generic value).
        
        Args:
            name: The business name to validate
            
        Returns:
            True if valid, False if it's a placeholder/invalid value
        """
        if not name:
            return False
        
        name_clean = str(name).strip().lower()
        
        # Invalid values that indicate extraction failed
        invalid_names = [
            'none', 'null', 'undefined', 'unknown',
            'results', 'result', 'search results',
            'google maps', 'map', 'maps',
            'loading', 'loading...', 
            'error', 'n/a', 'na',
            '', ' '
        ]
        
        if name_clean in invalid_names:
            return False
        
        # Too short (likely garbage)
        if len(name_clean) < 2:
            return False
        
        return True
    
    async def _create_context(self) -> BrowserContext:
        """Create a new browser context with randomized settings"""
        context = await self.browser.new_context(
            user_agent=self._get_random_user_agent(),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
        )
        return context
    
    async def scrape(
        self,
        query: str,
        target_count: int = None,
        max_scrolls: int = None,
        seen_places: Optional[set] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape Google Maps for a single query.
        
        Args:
            query: Search term (e.g., "dentists in Amritsar")
            target_count: How many unique cards to collect
            max_scrolls: Max scroll attempts
            seen_places: Set of Place IDs user has already scraped (for deduplication)
            
        Returns:
            List of unique business dictionaries
            
        Flow:
            1. Open Google Maps
            2. Search query
            3. Scroll to load cards (continue until stale)
            4. Collect ALL unique Place IDs from cards
            5. Filter out already-seen places (if seen_places provided)
            6. In parallel (4-5 at a time), extract details
            7. Deduplicate by Place ID
            8. Return results
        """
        target_count = target_count or settings.DEFAULT_TARGET_COUNT
        seen_places = seen_places or set()
        
        # Track dedup stats
        self.stats['skipped_duplicates'] = 0
        
        # Dynamic max_scrolls calculation based on target
        # Average: 8-10 cards per scroll, so target/8 scrolls needed
        # Add 50% buffer for safety: target/8 * 1.5 = target/5.3
        if max_scrolls is None:
            calculated_scrolls = max(20, int(target_count / 5))  # Minimum 20 scrolls
            max_scrolls = min(calculated_scrolls, 150)  # Cap at 150 to prevent infinite loops
            logger.info(f"📐 Auto-calculated max_scrolls: {max_scrolls} (based on target: {target_count})")
        else:
            logger.info(f"📌 Using provided max_scrolls: {max_scrolls}")
        
        if seen_places:
            logger.info(f"🔄 Deduplication: {len(seen_places)} previously scraped places will be skipped")
        
        logger.info(f"🔍 Starting scrape for query: '{query}' (target: {target_count})")
        logger.info(f"⚙️  Settings: max_scrolls={max_scrolls}, concurrent_cards={self.max_concurrent_cards}")
        
        # Update progress: Starting
        self._update_progress(
            status="scrolling",
            phase="Initializing scrape...",
            progress_percent=5
        )
        
        # Reset stats and dedup for new scrape
        self.stats = {
            'cards_found': 0,
            'cards_extracted': 0,
            'extraction_errors': 0,
            'scrolls_performed': 0,
            'stale_scrolls': 0
        }
        self.dedup_service.reset()
        
        # Ensure browser is started
        if not self.browser:
            await self.start()
        
        # Store search query for click-based extraction in parallel contexts
        self._current_search_query = query
        search_url = f"{GOOGLE_MAPS_SEARCH_URL}{query.replace(' ', '+')}"
        self._current_search_url = search_url
        
        # Create main context for search
        context = await self._create_context()
        page = await context.new_page()
        
        try:
            # Set timeout
            page.set_default_timeout(settings.BROWSER_TIMEOUT)
            
            # Update progress: Navigating
            self._update_progress(
                phase="Opening Google Maps...",
                progress_percent=8
            )
            
            # Navigate to Google Maps search
            logger.info(f"🌐 Navigating to: {search_url}")
            await page.goto(search_url, wait_until='networkidle')
            logger.info(f"✅ Page loaded successfully")
            
            # Update progress: Page loaded
            self._update_progress(
                phase="Searching for businesses...",
                progress_percent=12
            )
            
            # Wait for results to load
            await self._random_delay(*RATE_LIMIT['delay_after_search'])
            
            # Accept cookies if popup appears
            await self._handle_consent_popup(page)
            
            # Collect card links by scrolling
            # Collect MORE than target to account for dedup filtering (50% extra if we have seen places)
            buffer_multiplier = 1.5 if seen_places else 1.2
            collection_target = int(target_count * buffer_multiplier)
            logger.info(f"📜 Starting to collect card links (target: {target_count}, collecting: {collection_target} with buffer)...")
            
            # Update progress: Starting scroll
            self._update_progress(
                phase="Scrolling to find businesses...",
                progress_percent=15
            )
            
            card_links = await self._collect_unique_card_links(
                page,
                target_count=collection_target,
                max_scrolls=max_scrolls,
                seen_places=seen_places
            )
            
            logger.info(f"✅ Collected {len(card_links)} unique card links")
            self.stats['cards_found'] = len(card_links) + self.stats.get('skipped_duplicates', 0)
            
            # Extract details from cards in parallel
            logger.info(f"🔄 Starting parallel extraction of {len(card_links)} cards (skipped {self.stats.get('skipped_duplicates', 0)} duplicates)...")
            results = await self._extract_details_parallel(
                card_links,
                max_concurrent=self.max_concurrent_cards
            )
            
            # Limit to target count
            original_count = len(results)
            results = results[:target_count]
            if original_count > target_count:
                logger.info(f"✂️ Trimmed results from {original_count} to {target_count} (requested target)")
            
            # Update progress: Complete
            self._update_progress(
                status="completed",
                phase=f"✅ Complete! {len(results)} results found",
                progress_percent=100,
                unique_results=len(results),
                cards_extracted=self.stats['cards_extracted']
            )
            
            logger.info(f"✅ Scrape complete: {len(results)} unique results delivered")
            logger.info(f"📊 Final stats: {self.stats['cards_extracted']} extracted, {self.stats['extraction_errors']} errors")
            
            return results
            
        except Exception as e:
            logger.error(f"Scrape error: {e}")
            # Update progress: Failed
            self._update_progress(
                status="failed",
                phase=f"❌ Error: {str(e)[:50]}",
                error_message=str(e)
            )
            raise
        finally:
            await context.close()
    
    async def _handle_consent_popup(self, page: Page) -> None:
        """Handle Google consent popup if it appears"""
        try:
            # Look for "Accept all" button
            accept_button = page.locator('button:has-text("Accept all")')
            if await accept_button.count() > 0:
                await accept_button.first.click()
                await self._random_delay(1, 2)
                logger.info("Accepted consent popup")
        except Exception:
            pass  # Popup might not appear
    
    async def _collect_unique_card_links(
        self,
        page: Page,
        target_count: int,
        max_scrolls: int = 50,
        seen_places: Optional[set] = None
    ) -> Dict[str, Tuple[str, Optional[str]]]:
        """
        Scroll through results and collect unique card links.
        
        Args:
            page: Playwright page object
            target_count: Number of cards to collect
            max_scrolls: Maximum scroll attempts
            seen_places: Set of Place IDs user has already scraped (for deduplication)
            
        Returns:
            Dictionary mapping place_id to (href, card_name) tuple
            card_name is extracted from aria-label as fallback
            
        Stops scrolling when:
        - Reached target_count cards
        - Hit max_scrolls limit
        - 5 consecutive scrolls find 0 new cards (stale)
        - 15+ consecutive duplicate place_ids from seen_places (early exit optimization)
        """
        card_links: Dict[str, str] = {}
        seen_places = seen_places or set()
        stale_count = 0
        consecutive_seen_duplicates = 0  # Track consecutive cards that were already seen
        max_consecutive_seen = 15  # Stop if we see 15+ cards in a row that user already has
        
        for scroll_num in range(max_scrolls):
            self.stats['scrolls_performed'] += 1
            
            # Find all card links currently visible
            cards_before = len(card_links)
            scroll_seen_count = 0  # Count seen duplicates in this scroll
            scroll_new_count = 0   # Count new cards in this scroll
            
            try:
                # Get all result cards with href containing /maps/place/
                card_elements = await page.locator('a[href*="/maps/place/"]').all()
                
                for card in card_elements:
                    try:
                        href = await card.get_attribute('href')
                        if not href:
                            continue
                        
                        # Extract Place ID
                        place_id = self.dedup_service.extract_place_id(href)
                        
                        if not place_id:
                            continue
                        
                        # Skip if user has already scraped this place
                        if place_id in seen_places:
                            if place_id not in card_links:  # Only count once
                                self.stats['skipped_duplicates'] = self.stats.get('skipped_duplicates', 0) + 1
                                scroll_seen_count += 1
                                consecutive_seen_duplicates += 1
                            continue
                        
                        # Found a new card - reset consecutive counter
                        consecutive_seen_duplicates = 0
                        scroll_new_count += 1
                        
                        if place_id not in card_links:
                            # Also extract name from card's aria-label as a fallback
                            # The aria-label on the card usually contains the business name
                            card_name = None
                            try:
                                aria_label = await card.get_attribute('aria-label')
                                if aria_label and aria_label.strip():
                                    # aria-label is usually just the business name
                                    card_name = aria_label.strip()
                            except Exception:
                                pass
                            
                            # Store as tuple: (href, card_name)
                            card_links[place_id] = (href, card_name)
                            
                            if len(card_links) >= target_count:
                                logger.info(f"✅ Reached target count: {target_count}")
                                return card_links
                                
                    except Exception as e:
                        logger.debug(f"Error processing card: {e}")
                        continue
                
            except Exception as e:
                logger.warning(f"Error collecting cards on scroll {scroll_num}: {e}")
            
            # Early exit: Too many consecutive seen duplicates
            if consecutive_seen_duplicates >= max_consecutive_seen:
                logger.info(f"⛔ Early exit: {consecutive_seen_duplicates} consecutive cards already in user's database")
                logger.info(f"   → Skipped {self.stats.get('skipped_duplicates', 0)} duplicates, found {len(card_links)} new")
                self._update_progress(
                    phase=f"Stopped early - {len(card_links)} new businesses found",
                    cards_found=len(card_links)
                )
                break
            
            # Check for stale scroll
            cards_after = len(card_links)
            new_cards = cards_after - cards_before
            
            if new_cards == 0:
                stale_count += 1
                self.stats['stale_scrolls'] += 1
                
                # Better logging: show if cards were found but all were duplicates
                if scroll_seen_count > 0:
                    logger.info(f"⚠️  Scroll {scroll_num + 1}/{max_scrolls}: {scroll_seen_count} cards seen but all duplicates | Consecutive seen: {consecutive_seen_duplicates}")
                else:
                    logger.debug(f"⚠️  Scroll {scroll_num + 1}/{max_scrolls}: No new cards (stale: {stale_count}/{settings.STALE_SCROLL_LIMIT})")
                
                if stale_count >= settings.STALE_SCROLL_LIMIT:
                    logger.info(f"🛑 Stopping: {stale_count} stale scrolls in a row")
                    break
            else:
                stale_count = 0
                skipped_info = f" (skipped {scroll_seen_count} duplicates)" if scroll_seen_count > 0 else ""
                logger.info(f"📍 Scroll {scroll_num + 1}/{max_scrolls}: Found {new_cards} new cards{skipped_info} | Total: {cards_after}")
            
            # Update progress during scroll phase (0-30% of total progress)
            scroll_progress = 15 + int((scroll_num / max_scrolls) * 15)  # 15-30%
            skipped_duplicates = self.stats.get('skipped_duplicates', 0)
            self._update_progress(
                progress_percent=scroll_progress,
                phase=f"Scrolling... Found {cards_after} new, skipped {skipped_duplicates} duplicates",
                cards_found=cards_after,
                scrolls_done=scroll_num + 1
            )
            
            # Scroll down to load more
            await self._scroll_results_panel(page)
            await self._random_delay(*RATE_LIMIT['delay_between_scrolls'])
        
        return card_links
    
    async def _scroll_results_panel(self, page: Page) -> None:
        """Scroll the results panel to load more cards"""
        try:
            # Find the scrollable results container
            results_container = page.locator('div[role="feed"]')
            
            if await results_container.count() > 0:
                # Scroll within the container
                await results_container.evaluate(
                    'element => element.scrollBy(0, 500)'
                )
            else:
                # Fallback: Scroll the page
                await page.evaluate('window.scrollBy(0, 500)')
                
        except Exception as e:
            logger.debug(f"Scroll error: {e}")
            # Fallback scroll
            await page.keyboard.press('PageDown')
    
    async def _extract_details_parallel(
        self,
        card_links: Dict[str, Tuple[str, Optional[str]]],
        max_concurrent: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Extract details from multiple cards in parallel.
        
        Args:
            card_links: Dictionary mapping place_id to (href, card_name) tuple
            max_concurrent: Maximum concurrent extractions
            
        Returns:
            List of business detail dictionaries
        """
        results: List[Dict[str, Any]] = []
        semaphore = asyncio.Semaphore(max_concurrent)
        extracted_count = 0
        total_tasks = len(card_links)
        
        # Update progress: Starting extraction phase
        self._update_progress(
            status="extracting",
            phase=f"Extracting details from {total_tasks} businesses...",
            progress_percent=30,
            cards_found=total_tasks
        )
        
        async def extract_with_semaphore(place_id: str, href: str, card_name: Optional[str], index: int) -> Optional[Dict]:
            nonlocal extracted_count
            async with semaphore:
                try:
                    result = await self._extract_card_details(place_id, href, card_name)
                    if result:
                        extracted_count += 1
                        # Update progress (30-95% range for extraction)
                        extraction_progress = 30 + int((extracted_count / total_tasks) * 65)
                        self._update_progress(
                            progress_percent=extraction_progress,
                            phase=f"Extracting... {extracted_count}/{total_tasks} complete",
                            cards_extracted=extracted_count,
                            sample_result=result if result.get('name') else None
                        )
                    return result
                except Exception as e:
                    logger.error(f"Error extracting {place_id}: {e}")
                    self.stats['extraction_errors'] += 1
                    return None
        
        # Create extraction tasks - unpack (href, card_name) tuple
        tasks = [
            extract_with_semaphore(place_id, href_name[0], href_name[1], i)
            for i, (place_id, href_name) in enumerate(card_links.items())
        ]
        
        logger.info(f"🔄 Extracting {len(tasks)} cards with {max_concurrent} concurrent workers...")
        
        # Execute all tasks
        extracted = await asyncio.gather(*tasks)
        
        # Count successfully extracted
        extracted_count = sum(1 for r in extracted if r is not None)
        logger.info(f"✅ Extraction complete: {extracted_count}/{total_tasks} cards successfully extracted")
        
        # Update progress: Processing results
        self._update_progress(
            progress_percent=95,
            phase="Processing and deduplicating results..."
        )
        
        # Filter out None results and results without valid names
        skipped_no_name = 0
        for result in extracted:
            if result is None:
                continue
            
            # Use the new validation method
            name = result.get('name')
            if not self._is_valid_business_name(name):
                skipped_no_name += 1
                logger.warning(f"⚠️ Skipping result without valid name: place_id={result.get('place_id', 'unknown')[:20]}, got: '{name}'")
                continue
            
            # Check dedup one more time
            if self.dedup_service.add_place(
                place_id=result.get('place_id'),
                cid=result.get('cid'),
                href=result.get('href'),
                name=name,
                address=result.get('address')
            ):
                results.append(result)
                self.stats['cards_extracted'] += 1
        
        if skipped_no_name > 0:
            logger.warning(f"⚠️ Skipped {skipped_no_name} results without valid names")
        
        logger.info(f"✅ Valid results after filtering: {len(results)}")
        
        return results
    
    async def _extract_card_details(
        self,
        place_id: str,
        href: str,
        card_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract details by CLICKING the card, not navigating directly to URL.
        
        Why click-based extraction?
        - Google Maps requires the click interaction to trigger AJAX data loading
        - Direct URL navigation bypasses this, leaving you with skeleton HTML
        - Clicking the card populates the sidebar with full business details
        
        Args:
            place_id: The Place ID for this card
            href: Full URL to the place
            card_name: Business name from card's aria-label (fallback)
            
        Returns:
            Business details dictionary or None on error
        """
        context = await self._create_context()
        page = await context.new_page()
        
        try:
            page.set_default_timeout(settings.BROWSER_TIMEOUT)
            
            # Step 1: Navigate to the SEARCH RESULTS page first (not the place URL)
            # This is critical - we need to click from search results to trigger data loading
            if self._current_search_url:
                logger.debug(f"📍 Loading search results for card click: {place_id[:20]}")
                await page.goto(self._current_search_url, wait_until='domcontentloaded')
                
                # Wait for search results to load
                await page.wait_for_selector('a[href*="/maps/place/"]', timeout=10000)
                await self._random_delay(1.0, 2.0)
                
                # Handle consent popup if it appears
                await self._handle_consent_popup(page)
                
                # Step 2: Find and CLICK the specific card element with this place_id
                # Try multiple selector strategies
                card_clicked = False
                card_selectors = [
                    f'a[href*="{place_id}"]',  # Match by place_id in href
                    f'a[href*="/maps/place/"][href*="{place_id[:20]}"]',  # Partial match
                ]
                
                for card_selector in card_selectors:
                    try:
                        card_element = page.locator(card_selector).first
                        if await card_element.count() > 0:
                            # Scroll card into view first
                            await card_element.scroll_into_view_if_needed()
                            await self._random_delay(0.3, 0.6)
                            
                            # CLICK the card - this triggers Google's AJAX data loading!
                            await card_element.click()
                            card_clicked = True
                            logger.debug(f"🖱️ Clicked card: {place_id[:20]}")
                            break
                    except Exception as click_err:
                        logger.debug(f"Click attempt failed with selector {card_selector}: {click_err}")
                        continue
                
                if not card_clicked:
                    # Fallback: Try direct navigation with popstate simulation
                    logger.debug(f"⚠️ Card click failed, trying direct navigation with popstate: {place_id[:20]}")
                    full_url = href if href.startswith('http') else f"https://www.google.com{href}"
                    await page.goto(full_url, wait_until='domcontentloaded')
                    
                    # Simulate the click event Google expects
                    await page.evaluate("""
                        window.history.pushState({}, '', window.location.href);
                        window.dispatchEvent(new Event('popstate'));
                    """)
                
                # Step 3: Wait for sidebar to fully populate with business details
                # Google populates the sidebar AFTER click, not during page load
                try:
                    # Wait for actual business name content (not just h1 element)
                    await page.wait_for_function(
                        "document.querySelector('h1')?.textContent?.trim()?.length > 0",
                        timeout=8000
                    )
                except Exception:
                    logger.debug(f"⏱️ Timeout waiting for h1 content on {place_id[:20]}")
                
                # Wait for network to settle (AJAX calls completing)
                try:
                    await page.wait_for_load_state('networkidle', timeout=5000)
                except Exception:
                    pass
                
                # Additional delay for dynamic content
                await self._random_delay(2.0, 3.5)
                
            else:
                # Fallback if no search URL stored (shouldn't happen)
                logger.warning(f"No search URL stored, using direct navigation for {place_id[:20]}")
                full_url = href if href.startswith('http') else f"https://www.google.com{href}"
                await page.goto(full_url, wait_until='networkidle')
                await self._random_delay(3.0, 5.0)
            
            # Step 4: Extract from the NOW-POPULATED sidebar/page
            details = await self._extract_business_info(page)
            
            # Add identifiers
            details['place_id'] = place_id
            details['href'] = href
            
            # Try to extract CID
            cid = self.dedup_service.extract_cid_from_url(href)
            if cid:
                details['cid'] = cid
            
            # Use card_name as fallback if extraction failed
            name = details.get('name')
            if not name or not self._is_valid_business_name(name):
                if card_name and self._is_valid_business_name(card_name):
                    details['name'] = card_name
                    logger.debug(f"📝 Using card_name fallback: {card_name[:30]}")
            
            name = details.get('name', 'Unknown')
            rating = details.get('rating', 'N/A')
            reviews = details.get('reviews_count', 0)
            logger.info(f"✅ Extracted: {name} | ⭐ {rating} ({reviews} reviews)")
            
            return details
            
        except Exception as e:
            logger.error(f"❌ Error extracting {place_id}: {str(e)[:100]}")
            return None
        finally:
            await context.close()
    
    async def _extract_business_info(self, page: Page) -> Dict[str, Any]:
        """
        Extract all business information from the place page.
        Updated Jan 2026 with new Google Maps selectors.
        Uses aria-label extraction as primary method (Google's accessibility approach).
        
        Args:
            page: Playwright page object on a place detail page
            
        Returns:
            Dictionary with business information
        """
        info = {
            'name': None,
            'address': None,
            'phone': None,
            'website': None,
            'rating': None,
            'reviews_count': None,
            'category': None,
            'hours': None,
            'latitude': None,
            'longitude': None,
            'is_claimed': False,
            'photo_url': None
        }
        
        try:
            # === BUSINESS NAME EXTRACTION (Priority Order) ===
            # Method 1: Try aria-label on header elements first (most reliable in 2026)
            name_aria_selectors = [
                'div[role="main"] h1',           # Main content h1
                'h1[aria-label]',                 # H1 with aria-label
                '*[data-item-id*="title"]',      # Data attribute approach
            ]
            
            # Try aria-label extraction first
            for selector in name_aria_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        # Try aria-label attribute
                        aria_label = await element.get_attribute('aria-label')
                        if aria_label and aria_label.strip():
                            info['name'] = aria_label.strip()
                            break
                        # Fallback to text content
                        text = await element.inner_text()
                        if text and text.strip():
                            info['name'] = text.strip()
                            break
                except Exception:
                    continue
            
            # Method 2: Traditional CSS selectors if aria-label failed
            if not info['name']:
                name_selectors = [
                    "h1.DUwDvf.lfPIob",          # Primary selector (2026)
                    "h1.DUwDvf",                  # Simplified primary
                    "h1.fontHeadlineLarge",       # Fallback 1
                    "div.lMbq3e h1",              # Fallback 2  
                    "h1[class*='fontHeadline']",  # Pattern match
                    "div[role='main'] h1",        # Role-based
                    "h1",                         # Last resort
                ]
                info['name'] = await self._safe_get_text_chain(page, name_selectors)
            
            # Method 3: Extract from page title as ultimate fallback
            if not info['name']:
                try:
                    page_title = await page.title()
                    if page_title and ' - Google Maps' in page_title:
                        info['name'] = page_title.replace(' - Google Maps', '').strip()
                except Exception:
                    pass
            
            # Log diagnostic if name extraction failed
            if not info['name']:
                try:
                    # Get HTML snippet for debugging
                    html_snippet = await page.locator('body').first.inner_html()
                    logger.warning(f"⚠️ Failed to extract name. Page URL: {page.url}")
                    logger.debug(f"HTML snippet (first 800 chars): {html_snippet[:800]}")
                    # Log all h1 elements found
                    h1_elements = await page.locator('h1').all()
                    h1_texts = []
                    for h1 in h1_elements:
                        try:
                            h1_texts.append(await h1.inner_text())
                        except:
                            pass
                    if h1_texts:
                        logger.warning(f"H1 elements found: {h1_texts}")
                except Exception as diag_error:
                    logger.debug(f"Diagnostic logging failed: {diag_error}")
            
            # === RATING EXTRACTION (aria-label is most reliable) ===
            # Method 1: Extract from aria-label containing "stars" (most reliable)
            try:
                # Look for any element with aria-label containing star rating
                star_elements = await page.locator('*[aria-label*="star"]').all()
                for star_el in star_elements[:5]:  # Check first 5 matches
                    try:
                        aria_label = await star_el.get_attribute('aria-label')
                        if aria_label:
                            # Match patterns like "4.5 stars" or "4,5 stars"
                            rating_match = re.search(r'([\d.,]+)\s*star', aria_label, re.IGNORECASE)
                            if rating_match:
                                rating_str = rating_match.group(1).replace(',', '.')
                                info['rating'] = float(rating_str)
                                break
                    except Exception:
                        continue
            except Exception:
                pass
            
            # Method 2: Traditional selectors if aria-label failed
            if not info['rating']:
                rating_selectors = [
                    "div.F7nice span[aria-hidden='true']",  # Primary 2026
                    "span.ceNzKf[role='img']",              # Alternative
                    "div.fontBodyMedium span[aria-hidden='true']",  # Another variant
                ]
                for selector in rating_selectors:
                    try:
                        rating_el = page.locator(selector).first
                        if await rating_el.count() > 0:
                            rating_text = await rating_el.inner_text()
                            if rating_text:
                                # Clean and parse rating
                                rating_clean = rating_text.strip().replace(',', '.')
                                if rating_clean and rating_clean[0].isdigit():
                                    info['rating'] = float(rating_clean)
                                    break
                    except Exception:
                        continue
            
            # Reviews count - Updated selectors for 2026
            try:
                # Try getting reviews from button with aria-label
                reviews_el = page.locator("div.F7nice button[aria-label*='reviews']").first
                if await reviews_el.count() > 0:
                    aria_label = await reviews_el.get_attribute('aria-label')
                    if aria_label:
                        reviews_match = re.search(r'([\d,]+)', aria_label)
                        if reviews_match:
                            info['reviews_count'] = int(reviews_match.group(1).replace(',', ''))
            except Exception:
                pass
            
            if not info['reviews_count']:
                reviews_text = await self._safe_get_text(page, 'button[aria-label*="review"]')
                if not reviews_text:
                    reviews_text = await self._safe_get_text(page, 'span[aria-label*="review"]')
                if reviews_text:
                    reviews_match = re.search(r'([\d,]+)\s*review', reviews_text)
                    if reviews_match:
                        info['reviews_count'] = int(reviews_match.group(1).replace(',', ''))
            
            # Category - Updated selectors for 2026
            category_selectors = [
                "button.DkEaL",                   # Primary 2026
                "button[jsaction*='category']",   # Fallback
                "span.DkEaL",                     # Alternative
            ]
            info['category'] = await self._safe_get_text_chain(page, category_selectors)
            
            # === ADDRESS EXTRACTION (aria-label primary) ===
            # Method 1: aria-label containing "Address:"
            try:
                address_elements = await page.locator('*[aria-label*="Address"]').all()
                for addr_el in address_elements[:3]:
                    try:
                        aria_label = await addr_el.get_attribute('aria-label')
                        if aria_label and 'Address:' in aria_label:
                            info['address'] = aria_label.replace('Address:', '').strip()
                            break
                    except Exception:
                        continue
            except Exception:
                pass
            
            # Method 2: data-item-id approach
            if not info['address']:
                address_button = page.locator('button[data-item-id="address"]')
                if await address_button.count() > 0:
                    info['address'] = await self._safe_get_attribute(
                        page,
                        'button[data-item-id="address"]',
                        'aria-label'
                    )
                    if info['address']:
                        info['address'] = info['address'].replace('Address:', '').strip()
            
            # Method 3: Text-based fallback
            if not info['address']:
                info['address'] = await self._safe_get_text(
                    page,
                    'button[aria-label*="Address"]'
                )
                if info['address']:
                    info['address'] = info['address'].replace('Address:', '').strip()
            
            # === PHONE EXTRACTION (aria-label primary) ===
            # Method 1: aria-label containing "Phone:"
            try:
                phone_elements = await page.locator('*[aria-label*="Phone"]').all()
                for phone_el in phone_elements[:3]:
                    try:
                        aria_label = await phone_el.get_attribute('aria-label')
                        if aria_label and 'Phone:' in aria_label:
                            info['phone'] = aria_label.replace('Phone:', '').strip()
                            break
                    except Exception:
                        continue
            except Exception:
                pass
            
            # Method 2: data-item-id approach
            if not info['phone']:
                phone_button = page.locator('button[data-item-id*="phone"]')
                if await phone_button.count() > 0:
                    info['phone'] = await self._safe_get_attribute(
                        page,
                        'button[data-item-id*="phone"]',
                        'aria-label'
                    )
                    if info['phone']:
                        info['phone'] = info['phone'].replace('Phone:', '').strip()
            
            # Method 3: Text-based fallback
            if not info['phone']:
                info['phone'] = await self._safe_get_text(
                    page,
                    'button[aria-label*="Phone"]'
                )
                if info['phone']:
                    info['phone'] = info['phone'].replace('Phone:', '').strip()
            
            # Website
            website_link = page.locator('a[data-item-id="authority"]')
            if await website_link.count() > 0:
                info['website'] = await website_link.first.get_attribute('href')
            
            # Opening hours
            hours_element = page.locator('div[aria-label*="hour"]')
            if await hours_element.count() > 0:
                info['hours'] = await self._safe_get_attribute(
                    page,
                    'div[aria-label*="hour"]',
                    'aria-label'
                )
            
            # Is claimed
            claimed_element = page.locator('span:has-text("Claimed")')
            info['is_claimed'] = await claimed_element.count() > 0
            
            # Try to get coordinates from URL
            current_url = page.url
            coords_match = re.search(r'@(-?\d+\.?\d*),(-?\d+\.?\d*)', current_url)
            if coords_match:
                info['latitude'] = float(coords_match.group(1))
                info['longitude'] = float(coords_match.group(2))
            
            # Photo URL (main image)
            img_element = page.locator('img[decoding="async"]').first
            if await img_element.count() > 0:
                info['photo_url'] = await img_element.get_attribute('src')
                
        except Exception as e:
            logger.warning(f"Error extracting business info: {e}")
        
        return info
    
    async def _safe_get_text(self, page: Page, selector: str) -> Optional[str]:
        """Safely get text content from a selector"""
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                text = await element.text_content()
                return text.strip() if text else None
        except Exception:
            pass
        return None
    
    async def _safe_get_text_chain(self, page: Page, selectors: List[str]) -> Optional[str]:
        """
        Try multiple selectors until one returns text.
        Useful when Google changes their HTML structure.
        
        Args:
            page: Playwright page object
            selectors: List of CSS selectors to try in order
            
        Returns:
            Text content from the first matching selector, or None
        """
        for selector in selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    # Try inner_text first (more reliable for visible text)
                    text = await element.inner_text()
                    if text and text.strip():
                        return text.strip()
                    # Fallback to text_content
                    text = await element.text_content()
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue
        return None
    
    async def _safe_get_attribute(
        self,
        page: Page,
        selector: str,
        attribute: str
    ) -> Optional[str]:
        """Safely get an attribute from a selector"""
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                value = await element.get_attribute(attribute)
                return value.strip() if value else None
        except Exception:
            pass
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return {
            **self.stats,
            'dedup_stats': self.dedup_service.get_stats()
        }


# Convenience function for one-off scraping
async def scrape_google_maps(
    query: str,
    target_count: int = 50,
    max_scrolls: int = 50,
    max_concurrent: int = 4
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function to scrape Google Maps.
    
    Args:
        query: Search term
        target_count: Number of results to collect
        max_scrolls: Maximum scroll attempts
        max_concurrent: Concurrent card extractions
        
    Returns:
        Tuple of (results list, statistics dict)
    """
    async with GoogleMapsScraper(max_concurrent_cards=max_concurrent) as scraper:
        results = await scraper.scrape(
            query=query,
            target_count=target_count,
            max_scrolls=max_scrolls
        )
        return results, scraper.get_stats()
