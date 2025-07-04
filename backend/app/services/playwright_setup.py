"""
Playwright setup module for Windows compatibility and browser management
"""
import asyncio
import sys
from typing import Optional, List
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext
from app.utils.loggers import logger


# Global Playwright instance to avoid multiple initializations
_playwright_instance: Optional[Playwright] = None


def setup_windows_event_loop():
    """Set up proper event loop policy for Windows"""
    if sys.platform == "win32":
        try:
            # Try to use WindowsProactorEventLoopPolicy for better Windows compatibility
            if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                logger.info("Set Windows Proactor event loop policy")
            else:
                # Fallback to WindowsSelectorEventLoopPolicy
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                logger.info("Set Windows Selector event loop policy")
        except Exception as e:
            logger.warning(f"Could not set Windows event loop policy: {e}")


async def get_playwright() -> Playwright:
    """
    Get or create a Playwright instance with proper Windows configuration
    """
    global _playwright_instance
    
    if _playwright_instance is None:
        try:
            # Ensure proper event loop for Windows
            setup_windows_event_loop()
            
            # Install Playwright browsers if needed (in production, this should be done during deployment)
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"], 
                    capture_output=True, 
                    text=True,
                    timeout=120  # 2 minutes timeout
                )
                if result.returncode == 0:
                    logger.info("Playwright browsers installed/verified successfully")
                else:
                    logger.warning(f"Playwright install warning: {result.stderr}")
            except Exception as install_error:
                logger.warning(f"Could not verify Playwright installation: {install_error}")
            
            # Create Playwright instance
            _playwright_instance = await async_playwright().start()
            logger.info("Playwright instance created successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            raise
    
    return _playwright_instance


async def close_playwright(playwright: Optional[Playwright] = None):
    """
    Close Playwright instance and clean up resources
    """
    global _playwright_instance
    
    try:
        if playwright and playwright != _playwright_instance:
            await playwright.stop()
            logger.info("Provided Playwright instance closed")
        
        if _playwright_instance:
            await _playwright_instance.stop()
            _playwright_instance = None
            logger.info("Global Playwright instance closed")
            
    except Exception as e:
        logger.warning(f"Error closing Playwright: {e}")


def get_browser_args() -> List[str]:
    """
    Get browser launch arguments optimized for Windows and headless operation
    """
    args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        '--disable-background-networking',
        '--disable-sync',
        '--metrics-recording-only',
        '--no-default-browser-check',
        '--mute-audio',
        '--disable-extensions',
        '--disable-default-apps',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
    ]
    
    # Windows-specific arguments
    if sys.platform == "win32":
        args.extend([
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer',
            '--disable-background-timer-throttling'
        ])
    
    logger.info(f"Using browser args: {args}")
    return args


async def create_browser_context(browser: Browser) -> BrowserContext:
    """
    Create a browser context with optimal settings for scraping
    """
    try:
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060}  # NYC coordinates as default
        )
        
        # Set extra HTTP headers
        await context.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        logger.info("Browser context created successfully")
        return context
        
    except Exception as e:
        logger.error(f"Failed to create browser context: {e}")
        raise


async def cleanup_all():
    """
    Clean up all Playwright resources - call this on application shutdown
    """
    global _playwright_instance
    await close_playwright(_playwright_instance)
