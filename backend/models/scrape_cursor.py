"""
Scrape Session Cursor Model for Scrappy v2.0

Tracks pagination state for cursor-based scraping.
Allows resuming from where we left off instead of re-scrolling.

Why cursor-based pagination?
- User has 50-60 previously scraped places
- Instead of scrolling through ALL to find new ones
- We store scroll position and resume from there
- 10x faster incremental collection
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base


class ScrapeSessionCursor(Base):
    """
    Tracks pagination state for a user's query.
    Allows resuming from where we left off.
    
    Key insight: Google Maps returns cards in consistent order
    (geolocation-based, relevance-based). So if we store our
    scroll position, we can resume from there.
    
    TTL: 30 days - after that, cursor expires and fresh scrape starts.
    """
    __tablename__ = "scrape_session_cursors"
    
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # User reference (string to match BetterAuth user IDs)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Query normalization for semantic matching
    # "dentist in amritsar" and "amritsar dentist" should match
    query_hash = Column(String(64), nullable=False)  # MD5 hash of normalized query
    query_original = Column(String(500), nullable=False)  # "dentist amritsar"
    query_normalized = Column(String(500), nullable=False)  # normalized version
    
    # Pagination state - the core cursor data
    last_scroll_position = Column(Integer, default=0)  # DOM scroll height reached
    cards_collected = Column(Integer, default=0)  # Total cards seen in this query
    last_place_id = Column(String(64), nullable=True)  # Last place ID at cursor position
    last_card_index = Column(Integer, nullable=True)  # Card index in DOM for verification
    
    # Scroll metadata for accurate resumption
    total_scrolls_performed = Column(Integer, default=0)
    last_visible_card_count = Column(Integer, default=0)  # Cards visible when cursor saved
    
    # Extended cursor data (serialized for flexibility)
    cursor_data = Column(JSON, nullable=True)  # Store additional state if needed
    
    # Timestamps and TTL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # TTL: 30 days default
    
    # Indexes for fast lookups
    __table_args__ = (
        # Primary lookup: user + query combination
        Index('idx_cursor_user_query', 'user_id', 'query_hash'),
        # TTL cleanup: find expired cursors
        Index('idx_cursor_expires', 'expires_at'),
        # User's cursors for management
        Index('idx_cursor_user_updated', 'user_id', 'updated_at'),
    )
    
    def __repr__(self):
        return (
            f"<ScrapeSessionCursor user={self.user_id[:8]}... "
            f"query='{self.query_original[:30]}...' "
            f"cards={self.cards_collected} pos={self.last_scroll_position}>"
        )
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "query_original": self.query_original,
            "query_normalized": self.query_normalized,
            "cards_collected": self.cards_collected,
            "last_scroll_position": self.last_scroll_position,
            "last_place_id": self.last_place_id,
            "last_card_index": self.last_card_index,
            "total_scrolls_performed": self.total_scrolls_performed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
