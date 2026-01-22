"""
Models module for Scrappy v2.0

Import all models here to ensure Alembic can discover them
for auto-generating migrations.
"""

from database import Base

# Import current models so Alembic and other modules can discover them
from .user import User
from .better_auth import BetterAuthSession, BetterAuthUser
from .user_integration import UserIntegration
from .scrape_history import UserPlace, ScrapeSession, UserGoogleSheet

# Export all models
__all__ = [
    "Base",
    "User",
    "BetterAuthSession",
    "BetterAuthUser",
    "UserIntegration",
    "UserPlace",
    "ScrapeSession",
    "UserGoogleSheet",
]
