"""
Database Configuration for Scrappy v2.0

SQLAlchemy setup for PostgreSQL/Supabase
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create Base class for models
Base = declarative_base()

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Enable connection health checks
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """
    Get database session.
    
    Usage:
        @router.get("/")
        async def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    from models.user import User  # Import to register model
    from models.user_integration import UserIntegration  # Import for integration tables
    from models.scrape_history import UserPlace, ScrapeSession, UserGoogleSheet  # History/dedup tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created/verified")


def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("⚠️ All database tables dropped")
