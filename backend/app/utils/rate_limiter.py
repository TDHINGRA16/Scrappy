import time
import asyncio
from collections import defaultdict, deque
from typing import Dict, Optional
from dataclasses import dataclass
from app.utils.loggers import logger

@dataclass
class RateLimit:
    """Rate limit configuration"""
    max_requests: int
    window_seconds: int
    burst_allowance: int = 0  # Additional requests allowed in burst

class RateLimiter:
    """Thread-safe rate limiter using sliding window"""
    
    def __init__(self):
        self.limits: Dict[str, RateLimit] = {}
        self.windows: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    def configure(self, service: str, max_requests: int, window_seconds: int, burst_allowance: int = 0):
        """Configure rate limit for a service"""
        self.limits[service] = RateLimit(max_requests, window_seconds, burst_allowance)
        logger.info(f"Configured rate limit for {service}: {max_requests} req/{window_seconds}s")
    
    async def is_allowed(self, service: str, identifier: str = "default") -> bool:
        """Check if request is allowed under rate limit"""
        if service not in self.limits:
            return True  # No limit configured
        
        async with self.lock:
            key = f"{service}:{identifier}"
            limit = self.limits[service]
            current_time = time.time()
            window = self.windows[key]
            
            # Remove expired requests from window
            while window and window[0] <= current_time - limit.window_seconds:
                window.popleft()
            
            # Check if under limit
            requests_in_window = len(window)
            max_allowed = limit.max_requests + limit.burst_allowance
            
            if requests_in_window < max_allowed:
                window.append(current_time)
                return True
            
            logger.warning(f"Rate limit exceeded for {service}:{identifier}")
            return False
    
    async def wait_if_needed(self, service: str, identifier: str = "default") -> float:
        """Wait until request is allowed, returns wait time"""
        if service not in self.limits:
            return 0.0
        
        start_time = time.time()
        while not await self.is_allowed(service, identifier):
            await asyncio.sleep(0.1)  # Check every 100ms
        
        wait_time = time.time() - start_time
        if wait_time > 0:
            logger.info(f"Waited {wait_time:.2f}s for rate limit: {service}:{identifier}")
        
        return wait_time
    
    def get_stats(self, service: str, identifier: str = "default") -> Dict:
        """Get current rate limit statistics"""
        if service not in self.limits:
            return {"error": "Service not configured"}
        
        key = f"{service}:{identifier}"
        limit = self.limits[service]
        window = self.windows[key]
        current_time = time.time()
        
        # Count requests in current window
        active_requests = sum(
            1 for req_time in window 
            if req_time > current_time - limit.window_seconds
        )
        
        return {
            "service": service,
            "identifier": identifier,
            "active_requests": active_requests,
            "max_requests": limit.max_requests,
            "window_seconds": limit.window_seconds,
            "requests_remaining": max(0, limit.max_requests - active_requests),
            "reset_time": current_time + limit.window_seconds
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

# Configure default rate limits
def setup_default_limits():
    """Setup default rate limits for common services"""
    
    # SMTP rate limits (conservative to avoid being flagged as spam)
    rate_limiter.configure("smtp", max_requests=10, window_seconds=60)  # 10 emails per minute
    rate_limiter.configure("smtp_hourly", max_requests=100, window_seconds=3600)  # 100 emails per hour
    
    # Twilio WhatsApp limits
    rate_limiter.configure("twilio_whatsapp", max_requests=60, window_seconds=60)  # 60 per minute
    rate_limiter.configure("twilio_daily", max_requests=1000, window_seconds=86400)  # 1000 per day
    
    # Web scraping limits
    rate_limiter.configure("google_search", max_requests=10, window_seconds=60)  # Be nice to Google
    rate_limiter.configure("website_scrape", max_requests=30, window_seconds=60, burst_allowance=10)
    rate_limiter.configure("selenium", max_requests=5, window_seconds=60)  # Selenium is slower
    
    # API limits
    rate_limiter.configure("google_sheets", max_requests=100, window_seconds=100)  # Google Sheets API
    
    logger.info("Default rate limits configured")

# Convenience functions
async def check_rate_limit(service: str, identifier: str = "default") -> bool:
    """Check if request is allowed (non-blocking)"""
    return await rate_limiter.is_allowed(service, identifier)

async def wait_for_rate_limit(service: str, identifier: str = "default") -> float:
    """Wait for rate limit to allow request"""
    return await rate_limiter.wait_if_needed(service, identifier)

def get_rate_limit_stats(service: str, identifier: str = "default") -> Dict:
    """Get rate limit statistics"""
    return rate_limiter.get_stats(service, identifier)

# Decorator for rate-limited functions
def rate_limited(service: str, identifier_func=None):
    """Decorator to apply rate limiting to functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Determine identifier
            identifier = "default"
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            
            # Wait for rate limit
            await wait_for_rate_limit(service, identifier)
            
            # Execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Context manager for rate limiting
class rate_limit_context:
    """Context manager for rate limiting operations"""
    
    def __init__(self, service: str, identifier: str = "default"):
        self.service = service
        self.identifier = identifier
        self.wait_time = 0
    
    async def __aenter__(self):
        self.wait_time = await wait_for_rate_limit(self.service, self.identifier)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Batch processing with rate limiting
class RateLimitedBatch:
    """Process items in batches with rate limiting"""
    
    def __init__(self, service: str, batch_size: int = 10):
        self.service = service
        self.batch_size = batch_size
    
    async def process_items(self, items, process_func, identifier_func=None):
        """Process items in rate-limited batches"""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            for item in batch:
                identifier = "default"
                if identifier_func:
                    identifier = identifier_func(item)
                
                async with rate_limit_context(self.service, identifier):
                    try:
                        result = await process_func(item)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing item {item}: {str(e)}")
                        results.append(None)
        
        return results


# Add this to setup_default_limits function
rate_limiter.configure("website_scrape", max_requests=50, window_seconds=60)
# Initialize default limits
setup_default_limits()
