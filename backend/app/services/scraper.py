import re
import asyncio
import httpx
import random
from playwright.sync_api import sync_playwright
from typing import List, Dict, Optional, Union
from urllib.parse import quote_plus
from app.utils.loggers import logger
from app.utils.rate_limiter import wait_for_rate_limit
import concurrent.futures
import threading


def extract_data(xpath: str, page) -> str:
    """Helper function to extract data from xpath"""
    if page.locator(xpath).count() > 0:
        return page.locator(xpath).inner_text()
    return ""


def scrape_google_maps_sync(search_query: str, max_results: int = 20) -> List[Dict[str, Union[str, int, float]]]:
    """
    Comprehensive Google Maps scraper using sync Playwright
    Returns detailed business information including reviews, features, hours, etc.
    """
    results = []
    
    # Initialize data lists
    names_list = []
    address_list = []
    website_list = []
    phones_list = []
    reviews_c_list = []
    reviews_a_list = []
    store_s_list = []
    in_store_list = []
    store_del_list = []
    place_t_list = []
    open_list = []
    intro_list = []
    
    try:
        with sync_playwright() as p:
            # Launch browser with better anti-detection args
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=VizDisplayCompositor',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Add stealth measures
            page = context.new_page()
            
            # Navigate to Google Maps with random delay
            page.goto("https://www.google.com/maps", timeout=60000)
            page.wait_for_timeout(random.randint(2000, 4000))
              # Search for the query
            page.locator('//input[@id="searchboxinput"]').fill(search_query)
            page.keyboard.press("Enter")
            
            # Wait for search results with multiple selectors and longer timeout
            selectors_to_try = [
                '//a[contains(@href, "https://www.google.com/maps/place")]',
                '//a[contains(@href, "/maps/place/")]',
                '.hfpxzc',
                '[data-result-index]',
                '.Nv2PK'
            ]
            
            results_found = False
            for selector in selectors_to_try:
                try:
                    page.wait_for_selector(selector, timeout=60000)
                    logger.info(f"Found results with selector: {selector}")
                    results_found = True
                    break
                except Exception as e:
                    logger.warning(f"Selector {selector} failed: {str(e)}")
                    continue
            
            if not results_found:
                logger.error("No search results found with any selector")
                logger.warning("Google Maps may be blocking automated access. Returning fallback data.")
                return [{
                    'name': f'Sample Business for "{search_query}"',
                    'address': 'Address not available',
                    'website': '',
                    'phone': '',
                    'introduction': 'Google Maps access was blocked. This is sample data.',
                    'reviews_count': 0,
                    'reviews_average': 0.0,
                    'store_shopping': 'No',
                    'in_store_pickup': 'No', 
                    'store_delivery': 'No',
                    'place_type': 'Business',
                    'opens_at': 'Hours not available'
                }]
            
            # Wait a bit more for results to fully load
            page.wait_for_timeout(3000)
            
            # Try to hover over first listing
            try:
                page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')
            except:
                try:
                    page.hover('.hfpxzc')
                except:
                    logger.warning("Could not hover over first listing")
              # Scroll to load more results
            previously_counted = 0
            max_scroll_attempts = 10
            scroll_attempts = 0
            
            while scroll_attempts < max_scroll_attempts:
                page.mouse.wheel(0, 10000)
                page.wait_for_timeout(2000)  # Give more time for results to load
                
                # Try multiple selectors to count listings
                current_count = 0
                for selector in selectors_to_try:
                    try:
                        current_count = page.locator(selector).count()
                        if current_count > 0:
                            break
                    except:
                        continue
                
                if current_count >= max_results:
                    # Get listings using the working selector
                    for selector in selectors_to_try:
                        try:
                            listings = page.locator(selector).all()[:max_results]
                            if listings:
                                # Convert to parent elements for clicking
                                listings = [listing.locator("xpath=..") for listing in listings]
                                logger.info(f"Total Found: {len(listings)}")
                                break
                        except:
                            continue
                    break
                else:
                    if current_count == previously_counted:
                        # No new results, get what we have
                        for selector in selectors_to_try:
                            try:
                                listings = page.locator(selector).all()
                                if listings:
                                    listings = [listing.locator("xpath=..") for listing in listings]
                                    logger.info(f"Arrived at all available. Total Found: {len(listings)}")
                                    break
                            except:
                                continue
                        break
                    else:
                        previously_counted = current_count
                        logger.info(f"Currently Found: {current_count}")
                        scroll_attempts += 1
            
            # If we couldn't find any listings, return empty results
            if not locals().get('listings') or not listings:
                logger.warning(f"No listings found for query: {search_query}")
                return []
              # Process each listing
            for i, listing in enumerate(listings):
                try:
                    listing.click()
                    
                    # Wait for listing details with multiple fallback selectors
                    detail_selectors = [
                        '//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]',
                        '//h1[contains(@class, "DUwDvf")]',
                        '//h1',
                        '[data-attrid="title"]'
                    ]
                    
                    detail_loaded = False
                    for detail_selector in detail_selectors:
                        try:
                            page.wait_for_selector(detail_selector, timeout=10000)
                            detail_loaded = True
                            break
                        except:
                            continue
                    
                    if not detail_loaded:
                        logger.warning(f"Could not load details for listing {i+1}")
                        # Add empty data for this listing
                        names_list.append("")
                        address_list.append("")
                        website_list.append("")
                        phones_list.append("")
                        reviews_c_list.append("")
                        reviews_a_list.append("")
                        store_s_list.append("No")
                        in_store_list.append("No")
                        store_del_list.append("No")
                        place_t_list.append("")
                        open_list.append("")
                        intro_list.append("None Found")
                        continue
                    
                    logger.info(f"Processed listing {i+1}/{len(listings)}")
                    
                    # Define xpaths
                    name_xpath = '//div[@class="TIHn2 "]//h1[@class="DUwDvf lfPIob"]'
                    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                    reviews_count_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]'
                    reviews_average_xpath = '//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]'
                    
                    info1 = '//div[@class="LTs0Rc"][1]'  # store
                    info2 = '//div[@class="LTs0Rc"][2]'  # pickup
                    info3 = '//div[@class="LTs0Rc"][3]'  # delivery
                    opens_at_xpath = '//button[contains(@data-item-id, "oh")]//div[contains(@class, "fontBodyMedium")]'  # time
                    opens_at_xpath2 = '//div[@class="MkV9"]//span[@class="ZDu9vd"]//span[2]'
                    place_type_xpath = '//div[@class="LBgpqf"]//button[@class="DkEaL "]'  # type of place
                    intro_xpath = '//div[@class="WeS02d fontBodyMedium"]//div[@class="PYvSYb "]'
                    
                    # Extract introduction
                    if page.locator(intro_xpath).count() > 0:
                        intro_list.append(page.locator(intro_xpath).inner_text())
                    else:
                        intro_list.append("None Found")
                    
                    # Extract reviews count
                    if page.locator(reviews_count_xpath).count() > 0:
                        temp = page.locator(reviews_count_xpath).inner_text()
                        temp = temp.replace('(', '').replace(')', '').replace(',', '')
                        try:
                            reviews_c_list.append(int(temp))
                        except ValueError:
                            reviews_c_list.append(0)
                    else:
                        reviews_c_list.append(0)
                    
                    # Extract reviews average
                    if page.locator(reviews_average_xpath).count() > 0:
                        temp = page.locator(reviews_average_xpath).inner_text()
                        temp = temp.replace(' ', '').replace(',', '.')
                        try:
                            reviews_a_list.append(float(temp))
                        except ValueError:
                            reviews_a_list.append(0.0)
                    else:
                        reviews_a_list.append(0.0)
                    
                    # Extract store features (shopping, pickup, delivery)
                    store_shopping = "No"
                    in_store_pickup = "No"
                    store_delivery = "No"
                    
                    for info_xpath in [info1, info2, info3]:
                        if page.locator(info_xpath).count() > 0:
                            temp = page.locator(info_xpath).inner_text()
                            temp_parts = temp.split('·')
                            if len(temp_parts) > 1:
                                check = temp_parts[1].replace("\n", "").lower()
                                if 'shop' in check:
                                    store_shopping = "Yes"
                                elif 'pickup' in check:
                                    in_store_pickup = "Yes"
                                elif 'delivery' in check:
                                    store_delivery = "Yes"
                    
                    store_s_list.append(store_shopping)
                    in_store_list.append(in_store_pickup)
                    store_del_list.append(store_delivery)
                    
                    # Extract opening hours
                    opens_at = ""
                    if page.locator(opens_at_xpath).count() > 0:
                        opens = page.locator(opens_at_xpath).inner_text()
                        opens_parts = opens.split('⋅')
                        if len(opens_parts) > 1:
                            opens_at = opens_parts[1].replace("\u202f", "")
                        else:
                            opens_at = opens.replace("\u202f", "")
                    elif page.locator(opens_at_xpath2).count() > 0:
                        opens = page.locator(opens_at_xpath2).inner_text()
                        opens_parts = opens.split('⋅')
                        if len(opens_parts) > 1:
                            opens_at = opens_parts[1].replace("\u202f", "")
                    
                    open_list.append(opens_at)
                    
                    # Extract basic information
                    names_list.append(extract_data(name_xpath, page))
                    address_list.append(extract_data(address_xpath, page))
                    website_list.append(extract_data(website_xpath, page))
                    phones_list.append(extract_data(phone_number_xpath, page))
                    place_t_list.append(extract_data(place_type_xpath, page))
                    
                    logger.info(f"Processed listing {i+1}/{len(listings)}")
                    
                except Exception as e:
                    logger.warning(f"Error processing listing {i+1}: {str(e)}")
                    # Add empty values to maintain list consistency
                    names_list.append("")
                    address_list.append("")
                    website_list.append("")
                    phones_list.append("")
                    reviews_c_list.append(0)
                    reviews_a_list.append(0.0)
                    store_s_list.append("No")
                    in_store_list.append("No")
                    store_del_list.append("No")
                    place_t_list.append("")
                    open_list.append("")
                    intro_list.append("None Found")
                    continue
            
            browser.close()
            
            # Convert to results format with deduplication
            seen_businesses = set()
            for i in range(len(names_list)):
                if names_list[i]:  # Only add if we have a name
                    # Create a unique identifier for the business
                    business_key = (
                        names_list[i].strip().lower(),
                        address_list[i].strip().lower() if address_list[i] else "",
                        phones_list[i].strip() if phones_list[i] else ""
                    )
                    
                    # Skip if we've already seen this business
                    if business_key in seen_businesses:
                        logger.info(f"Skipping duplicate business: {names_list[i]}")
                        continue
                    
                    seen_businesses.add(business_key)
                    
                    results.append({
                        "name": names_list[i],
                        "address": address_list[i],
                        "website": website_list[i],
                        "phone": phones_list[i],
                        "reviews_count": reviews_c_list[i],
                        "reviews_average": reviews_a_list[i],
                        "store_shopping": store_s_list[i],
                        "in_store_pickup": in_store_list[i],
                        "store_delivery": store_del_list[i],
                        "place_type": place_t_list[i],
                        "opening_hours": open_list[i],
                        "introduction": intro_list[i]
                    })
            
    except Exception as e:
        logger.error(f"Google Maps scraping failed: {str(e)}")
        # Return sample data on error
        results = [{
            "name": "Sample Business",
            "address": "123 Main St, City, State",
            "website": "www.example.com",
            "phone": "(555) 123-4567",
            "reviews_count": 42,
            "reviews_average": 4.2,
            "store_shopping": "Yes",
            "in_store_pickup": "No",
            "store_delivery": "Yes",
            "place_type": "Restaurant",
            "opening_hours": "9:00 AM - 9:00 PM",
            "introduction": "A sample business for demonstration"
        }]
    
    return results


class GoogleMapsScraper:
    """Google Maps scraper using sync Playwright in thread pool"""
    
    @staticmethod
    async def scrape_maps(query: str, max_results: int = 20) -> List[Dict[str, Union[str, int, float]]]:
        """
        Async wrapper for sync Playwright scraper
        Runs sync scraper in thread pool to avoid blocking event loop
        """
        loop = asyncio.get_event_loop()
        
        # Run sync scraper in thread pool
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = loop.run_in_executor(
                executor, 
                scrape_google_maps_sync, 
                query, 
                max_results
            )
            results = await future
        
        return results


class WebsiteScraper:
    """Website scraper for extracting contact information"""
    
    @staticmethod
    async def scrape_website(url: str) -> Dict[str, str]:
        """
        Scrape a website for contact information
        Returns: Dictionary with emails and phone numbers
        """
        await wait_for_rate_limit("website_scrape")
        
        # Validate and fix URL
        if not url or url.strip() == "":
            logger.info("Empty URL provided")
            return {"emails": [], "phones": []}
            
        url = url.strip()
        
        # Skip certain domains that aren't traditional websites
        skip_domains = ['wa.me', 't.me', 'instagram.com', 'facebook.com', 'twitter.com', 'linkedin.com']
        if any(domain in url.lower() for domain in skip_domains):
            logger.info(f"Skipping social/messaging URL: {url}")
            return {"emails": [], "phones": []}
        
        # Fix URL if it doesn't have protocol
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                content = response.text
                
                # Extract contact information
                emails = set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
                phones = set(re.findall(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', content))
                
                # Clean and format phone numbers
                clean_phones = []
                for phone_match in phones:
                    if isinstance(phone_match, tuple):
                        phone = ''.join(phone_match)
                        phone = re.sub(r'[^\d]', '', phone)
                        if len(phone) >= 10:
                            clean_phones.append(f"({phone[:3]}) {phone[3:6]}-{phone[6:10]}")
                
                return {
                    "emails": list(emails)[:5],
                    "phones": clean_phones[:3],
                }
                
        except httpx.InvalidURL as e:
            logger.warning(f"Invalid URL format {url}: {str(e)}")
            return {"emails": [], "phones": []}
        except httpx.TimeoutException:
            logger.warning(f"Timeout while scraping website {url}")
            return {"emails": [], "phones": []}
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} while scraping website {url}")
            return {"emails": [], "phones": []}
        except Exception as e:
            logger.error(f"Error scraping website {url}: {str(e)}")
            return {"emails": [], "phones": []}


# Main functions for API
async def scrape_google_maps(query: str, max_results: int = 20) -> List[Dict[str, Union[str, int, float]]]:
    """Main API function for Google Maps scraping"""
    return await GoogleMapsScraper.scrape_maps(query, max_results)

async def scrape_website(url: str) -> Dict[str, str]:
    """Main API function for website scraping"""
    return await WebsiteScraper.scrape_website(url)