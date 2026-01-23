"""
Configuration & Constants for Scrappy v2.0
All settings loaded from environment variables with sensible defaults
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # FastAPI
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Scraper Settings
    MAX_CONCURRENT_CARDS: int = 4  # 4-5 cards extracted in parallel
    MAX_SCROLLS: int = 50  # Maximum scroll attempts
    STALE_SCROLL_LIMIT: int = 5  # Stop after N scrolls with 0 new cards
    DEFAULT_TARGET_COUNT: int = 50  # Default number of results
    SCROLL_DELAY_MIN: float = 1.0  # Minimum delay between scrolls (seconds)
    SCROLL_DELAY_MAX: float = 3.0  # Maximum delay between scrolls (seconds)
    CARD_EXTRACT_DELAY_MIN: float = 0.5  # Min delay between card extractions
    CARD_EXTRACT_DELAY_MAX: float = 1.5  # Max delay between card extractions
    
    # Browser Settings
    HEADLESS: bool = True
    BROWSER_TIMEOUT: int = 60000  # 60 seconds
    PAGE_LOAD_TIMEOUT: int = 60000  # 60 seconds
    
    # User Agent Rotation
    USER_AGENTS: list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]
    
    # Google Sheets (Legacy - service account)
    GOOGLE_SHEETS_CREDENTIALS_JSON: Optional[str] = None
    SPREADSHEET_ID: Optional[str] = None
    
    # Google OAuth 2.0 (Per-user authentication)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/integrations/google/callback"
    
    # Encryption (for storing OAuth tokens)
    ENCRYPTION_KEY: Optional[str] = None
    
    # SMS Settings
    SMS_PROVIDER: str = "twilio"  # "twilio" or "fast2sms"
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Fast2SMS
    FAST2SMS_API_KEY: Optional[str] = None
    FAST2SMS_SENDER_ID: Optional[str] = None
    
    # WhatsApp Cloud API (shared account for users without their own)
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    
    # Database (PostgreSQL/Supabase)
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/scrappy"
    
    # JWT & Authentication (BetterAuth - replaces hardcoded auth)
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Origins (for frontend)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def cors_origins_list(self) -> list:
        """Parse CORS_ORIGINS string into list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()


# Constants for scraping
GOOGLE_MAPS_URL = "https://www.google.com/maps"
GOOGLE_MAPS_SEARCH_URL = "https://www.google.com/maps/search/"

# CSS Selectors for Google Maps (may need updates if Google changes UI)
SELECTORS = {
    # Search
    "search_box": 'input[id="searchboxinput"]',
    "search_button": 'button[id="searchbox-searchbutton"]',
    
    # Results panel
    "results_container": 'div[role="feed"]',
    "result_card": 'a[href*="/maps/place/"]',
    "result_card_container": 'div[jsaction*="mouseover:pane"]',
    
    # Card details (when clicked)
    "business_name": 'h1',
    "rating": 'div[role="img"][aria-label*="stars"]',
    "reviews_count": 'span[aria-label*="reviews"]',
    "category": 'button[jsaction*="category"]',
    "address": 'button[data-item-id="address"]',
    "phone": 'button[data-item-id*="phone"]',
    "website": 'a[data-item-id="authority"]',
    "hours": 'div[aria-label*="hours"]',
    "claimed_badge": 'span[aria-label*="Claimed"]',
    
    # Alternative selectors (backup)
    "address_alt": 'button[aria-label*="Address"]',
    "phone_alt": 'button[aria-label*="Phone"]',
    "website_alt": 'a[aria-label*="Website"]',
}

# Rate limiting settings
RATE_LIMIT = {
    "places_per_session": 120,  # Google's approximate limit
    "delay_between_cards": (0.5, 1.5),  # Random delay range in seconds
    "delay_between_scrolls": (1.0, 3.0),  # Random delay range in seconds
    "delay_after_search": (2.0, 4.0),  # Wait for results to load
}
