"""
Browser Session Pool Manager for Scrappy v2.0

Manages per-user isolated browser sessions for concurrent scraping.
Each user gets their own browser context with isolated cookies, cache, and state.

Features:
- One browser context per user (no interference between users)
- Auto-cleanup of idle sessions (configurable timeout)
- Resource limits (max concurrent sessions)
- Thread-safe with asyncio locks
- Graceful shutdown handling
"""

import sys
import asyncio
import random
import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from config import settings

# Fix for Windows
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """Represents an active browser session for a user."""
    context: BrowserContext
    page: Page
    last_activity: datetime
    created_at: datetime
    scrape_count: int = 0
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        self.scrape_count += 1


class BrowserSessionPool:
    """
    Manages per-user isolated browser sessions for concurrent scraping.

    Architecture:
    - Single Playwright instance shared across all users
    - Single Browser instance with multiple isolated contexts
    - Each user gets their own BrowserContext (isolated cookies, localStorage, cache)
    - Sessions auto-cleanup after idle timeout
    
    Benefits:
    - User A and User B can scrape simultaneously without interference
    - Each user's Google Maps state is isolated
    - Memory efficient (reuses browser instance)
    - Auto-scales down when idle
    """

    def __init__(
        self, 
        max_sessions: int = 20, 
        idle_timeout_minutes: int = 30,
        session_max_age_minutes: int = 120
    ):
        """
        Initialize the browser session pool.
        
        Args:
            max_sessions: Maximum concurrent browser sessions
            idle_timeout_minutes: Close sessions after N minutes of inactivity
            session_max_age_minutes: Force close sessions after N minutes (prevent memory leaks)
        """
        self.max_sessions = max_sessions
        self.idle_timeout = timedelta(minutes=idle_timeout_minutes)
        self.session_max_age = timedelta(minutes=session_max_age_minutes)

        # Session storage: {user_id: UserSession}
        self.sessions: Dict[str, UserSession] = {}

        # Shared Playwright/Browser instances
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None

        # Thread safety
        self.lock = asyncio.Lock()
        
        # Background cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False

        logger.info(
            f"BrowserSessionPool initialized: max_sessions={max_sessions}, "
            f"idle_timeout={idle_timeout_minutes}min, max_age={session_max_age_minutes}min"
        )

    async def initialize(self) -> None:
        """Initialize Playwright and browser instance."""
        if self.playwright:
            return  # Already initialized
            
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=settings.HEADLESS,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                ]
            )
            logger.info("✅ Browser session pool initialized")

            # Start background cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser pool: {e}")
            raise

    def _get_random_user_agent(self) -> str:
        """Get a random user agent."""
        return random.choice(settings.USER_AGENTS)

    async def get_session(self, user_id: str) -> Tuple[BrowserContext, Page]:
        """
        Get or create isolated browser session for user.

        Args:
            user_id: User ID (string format)

        Returns:
            Tuple of (BrowserContext, Page) for the user

        Raises:
            RuntimeError: If max sessions reached and no cleanup possible
        """
        async with self.lock:
            # Ensure browser is initialized
            if not self.browser:
                await self.initialize()

            # Check if user already has active session
            if user_id in self.sessions:
                session = self.sessions[user_id]
                session.update_activity()
                logger.debug(f"♻️ Reusing session for user {user_id}")
                return session.context, session.page

            # Check session limit
            if len(self.sessions) >= self.max_sessions:
                # Try cleanup first
                await self._cleanup_idle_sessions_sync()

                # Still at limit?
                if len(self.sessions) >= self.max_sessions:
                    raise RuntimeError(
                        f"Maximum concurrent sessions ({self.max_sessions}) reached. "
                        "Please try again in a few minutes."
                    )

            # Create new isolated context for user
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self._get_random_user_agent(),
                locale='en-US',
                timezone_id='America/New_York',
                ignore_https_errors=True,
                java_script_enabled=True,
            )

            # Anti-detection: Override navigator properties
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            """)

            # Create new page in context
            page = await context.new_page()
            page.set_default_timeout(settings.BROWSER_TIMEOUT)

            # Create session object
            now = datetime.utcnow()
            session = UserSession(
                context=context,
                page=page,
                last_activity=now,
                created_at=now
            )

            # Store session
            self.sessions[user_id] = session
            logger.info(f"✨ Created new session for user {user_id} (total: {len(self.sessions)})")

            return context, page

    async def release_session(self, user_id: str) -> None:
        """
        Release (close) user's browser session immediately.

        Args:
            user_id: User ID
        """
        async with self.lock:
            if user_id not in self.sessions:
                return

            session = self.sessions[user_id]
            await self._close_session(user_id, session)

    async def _close_session(self, user_id: str, session: UserSession) -> None:
        """Close a single session (must be called within lock)."""
        try:
            await session.page.close()
        except Exception as e:
            logger.debug(f"Error closing page for user {user_id}: {e}")

        try:
            await session.context.close()
        except Exception as e:
            logger.debug(f"Error closing context for user {user_id}: {e}")

        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"🗑️ Released session for user {user_id} (remaining: {len(self.sessions)})")

    async def _cleanup_idle_sessions_sync(self) -> int:
        """
        Cleanup idle and expired sessions (called within lock).
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        to_cleanup = []

        for user_id, session in self.sessions.items():
            idle_duration = now - session.last_activity
            age = now - session.created_at

            # Cleanup if idle too long OR too old
            if idle_duration > self.idle_timeout or age > self.session_max_age:
                to_cleanup.append((user_id, session, "idle" if idle_duration > self.idle_timeout else "max_age"))

        for user_id, session, reason in to_cleanup:
            logger.info(f"🧹 Cleaning up session for user {user_id} (reason: {reason})")
            await self._close_session(user_id, session)

        return len(to_cleanup)

    async def _cleanup_loop(self) -> None:
        """Background task to periodically clean up idle sessions."""
        while not self._shutdown:
            try:
                await asyncio.sleep(60)  # Check every minute

                if self._shutdown:
                    break

                async with self.lock:
                    cleaned = await self._cleanup_idle_sessions_sync()
                    if cleaned > 0:
                        logger.info(f"🧹 Background cleanup: {cleaned} sessions removed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def shutdown(self) -> None:
        """Shutdown all sessions and browser."""
        logger.info("🛑 Shutting down browser session pool...")
        self._shutdown = True

        async with self.lock:
            # Close all sessions
            for user_id, session in list(self.sessions.items()):
                await self._close_session(user_id, session)

            self.sessions.clear()

            # Close browser
            if self.browser:
                try:
                    await self.browser.close()
                except Exception as e:
                    logger.debug(f"Error closing browser: {e}")
                self.browser = None

            # Stop Playwright
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception as e:
                    logger.debug(f"Error stopping playwright: {e}")
                self.playwright = None

        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("✅ Browser session pool shut down")

    def get_active_sessions_count(self) -> int:
        """Get number of active sessions."""
        return len(self.sessions)

    def get_session_info(self) -> Dict[str, Any]:
        """Get session pool statistics."""
        now = datetime.utcnow()
        
        sessions_info = {}
        for user_id, session in self.sessions.items():
            idle_minutes = (now - session.last_activity).total_seconds() / 60
            age_minutes = (now - session.created_at).total_seconds() / 60
            
            sessions_info[user_id] = {
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'idle_minutes': round(idle_minutes, 1),
                'age_minutes': round(age_minutes, 1),
                'scrape_count': session.scrape_count
            }

        return {
            'active_sessions': len(self.sessions),
            'max_sessions': self.max_sessions,
            'available_slots': self.max_sessions - len(self.sessions),
            'idle_timeout_minutes': self.idle_timeout.total_seconds() / 60,
            'sessions': sessions_info
        }

    async def reset_session(self, user_id: str) -> Tuple[BrowserContext, Page]:
        """
        Force reset user's session (close and create new).
        Useful if session becomes corrupted.
        
        Args:
            user_id: User ID
            
        Returns:
            New (BrowserContext, Page) tuple
        """
        await self.release_session(user_id)
        return await self.get_session(user_id)


# Global singleton instance
browser_pool = BrowserSessionPool(
    max_sessions=20,
    idle_timeout_minutes=30,
    session_max_age_minutes=120
)
