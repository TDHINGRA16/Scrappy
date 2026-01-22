"""
Scrape History Models for Scrappy v2.0

SQLAlchemy models for storing:
- User Place IDs (for deduplication)
- Scrape sessions (for history UI)
- User Google Sheets mapping

Storage strategy:
- Only Place IDs stored in DB (~50 bytes/business)
- Full data stored in user's Google Sheets
- Infinite scaling, minimal cost
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base


class UserPlace(Base):
    """
    Stores Place IDs for each user - used for deduplication.
    
    Storage: ~50 bytes per business
    - 1K users * 5K businesses = 250MB total
    - Cost: ~$0.50/month at scale
    """
    __tablename__ = "user_places"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User reference (string to match BetterAuth user IDs)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Place identifiers (primary dedup key)
    place_id = Column(String(64), nullable=False)  # e.g., 0x890cb024fe77e7b6
    cid = Column(String(64), nullable=True)        # Fallback identifier
    
    # Query tracking
    query_hash = Column(String(255), nullable=True)  # query_YYYYMMDD
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scraped_count = Column(Integer, default=1)
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'place_id', name='uix_user_place'),
        Index('idx_user_places_lookup', 'user_id', 'place_id'),
        Index('idx_user_query_hash', 'user_id', 'query_hash'),
    )
    
    def __repr__(self):
        return f"<UserPlace user={self.user_id[:8]}... place={self.place_id[:16]}...>"


class ScrapeSession(Base):
    """
    Records each scraping session for history UI.
    
    Links to Google Sheets where full data is stored.
    """
    __tablename__ = "scrape_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(String(255), nullable=False, index=True)
    
    # Query info
    query = Column(String(500), nullable=False)
    query_hash = Column(String(255), nullable=True)
    
    # Results summary
    total_found = Column(Integer, default=0)        # Cards found before dedup
    new_results = Column(Integer, default=0)        # NEW results extracted
    skipped_duplicates = Column(Integer, default=0) # Duplicates skipped
    extraction_errors = Column(Integer, default=0)
    
    # Google Sheet reference (where full data lives)
    sheet_id = Column(String(255), nullable=True)
    sheet_url = Column(Text, nullable=True)
    sheet_name = Column(String(255), nullable=True)
    
    # Performance metrics
    time_taken_seconds = Column(Integer, default=0)
    scrolls_performed = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_session_user_date', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ScrapeSession {self.id} query='{self.query[:30]}...'>"


class UserGoogleSheet(Base):
    """
    Maps users to their default Google Sheet for scraping results.
    
    Each user has ONE sheet where all results are appended.
    """
    __tablename__ = "user_google_sheets"
    
    user_id = Column(String(255), primary_key=True)
    
    # Google Sheet info
    sheet_id = Column(String(255), nullable=False)
    sheet_name = Column(String(255), nullable=True, default="Scrappy Results")
    sheet_url = Column(Text, nullable=True)
    
    # Permissions
    has_write_access = Column(Integer, default=1)  # Boolean as int for compatibility
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<UserGoogleSheet user={self.user_id[:8]}... sheet={self.sheet_id[:16]}...>"
