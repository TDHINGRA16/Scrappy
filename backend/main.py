"""
Scrappy v2.0 - Google Maps Lead Scraper
FastAPI Backend with BetterAuth Authentication

Run with: python run.py (Windows) or uvicorn main:app --reload (Linux/Mac)
"""

import sys
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from routes.scraping import router as scraping_router
from routes.health import router as health_router
from routes.auth import router as auth_router
from routes.integrations import router as integrations_router
from routes.whatsapp import router as whatsapp_router
from services.browser_session_pool import browser_pool
from config import settings
from database import create_tables

# Fix for Windows: Set the event loop policy for Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Scrappy v2.0 Starting...")
    
    # Initialize database tables
    try:
        create_tables()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization skipped: {e}")
        logger.info("   (Set DATABASE_URL in .env for full auth support)")
    
    # Initialize browser session pool
    try:
        await browser_pool.initialize()
        logger.info("✅ Browser session pool initialized")
    except Exception as e:
        logger.warning(f"⚠️ Browser pool initialization failed: {e}")
    
    yield
    
    # Shutdown browser pool
    try:
        await browser_pool.shutdown()
        logger.info("✅ Browser session pool shut down")
    except Exception as e:
        logger.warning(f"⚠️ Browser pool shutdown error: {e}")
    
    logger.info("🛑 Scrappy v2.0 Shutting down...")


app = FastAPI(
    title="Scrappy v2.0",
    description="Google Maps Lead Scraper API with BetterAuth Authentication",
    version="2.0.0",
    lifespan=lifespan
)

# CORS - Use configured origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(auth_router)  # /api/auth/* routes
app.include_router(scraping_router, prefix="/api", tags=["Scraping"])
app.include_router(integrations_router, prefix="/api/integrations/google", tags=["Integrations"])
app.include_router(whatsapp_router, tags=["WhatsApp"])


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Scrappy v2.0 API",
        "version": "2.0.0",
        "description": "Google Maps Lead Scraper - Auth handled by BetterAuth (Next.js)",
        "docs": "/docs",
        "health": "/health",
        "note": "Authentication is handled by BetterAuth in the Next.js frontend at localhost:3000/api/auth",
        "integrations": {
            "google_sheets": {
                "authorize": "/api/integrations/google/authorize",
                "callback": "/api/integrations/google/callback",
                "status": "/api/integrations/google/status",
                "save": "/api/integrations/google/save-to-sheet",
                "disconnect": "/api/integrations/google/disconnect"
            },
            "whatsapp": {
                "connect": "/api/whatsapp/connect",
                "status": "/api/whatsapp/status",
                "send": "/api/whatsapp/send",
                "send_bulk": "/api/whatsapp/send-bulk",
                "templates": "/api/whatsapp/templates",
                "disconnect": "/api/whatsapp/disconnect"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
