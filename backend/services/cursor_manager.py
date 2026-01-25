"""
Cursor Manager Service for Scrappy v2.0

Manages pagination cursors for users.
Allows resuming scrapes from where we left off.

Benefits:
- 10x faster incremental collection
- No re-scrolling through old data
- Scales to 5,000+ results
- Persistent across sessions (30-day TTL)

Usage:
    cursor_manager = CursorManager(db)
    
    # Get existing cursor or create new one
    cursor = cursor_manager.get_or_create_cursor(user_id, query)
    
    # After scrape, update cursor
    cursor_manager.update_cursor(
        user_id=user_id,
        query=query,
        cards_collected=150,
        last_scroll_position=5000,
        last_place_id="0x890cb024fe77e7b6"
    )
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.scrape_cursor import ScrapeSessionCursor
from services.query_normalizer import QueryNormalizer

logger = logging.getLogger(__name__)


class CursorManager:
    """
    Manages pagination cursors for users.
    
    Each cursor tracks:
    - Scroll position (DOM scroll height)
    - Cards collected so far
    - Last place ID (for anchor verification)
    - Query normalization (for semantic matching)
    
    TTL: Cursors expire after 30 days of inactivity.
    """
    
    # Cursor TTL in days - after this, cursor expires and fresh scrape starts
    CURSOR_TTL_DAYS = 30
    
    def __init__(self, db: Session):
        """
        Initialize CursorManager with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.normalizer = QueryNormalizer()
    
    def get_cursor(
        self, 
        user_id: str, 
        query: str
    ) -> Optional[ScrapeSessionCursor]:
        """
        Get cursor for this user/query combination.
        
        Performs semantic query matching using normalized hash.
        
        Args:
            user_id: User identifier
            query: Search query (will be normalized)
            
        Returns:
            ScrapeSessionCursor if found and not expired, None otherwise
        """
        query_hash = self.normalizer.get_hash(query)
        query_normalized = self.normalizer.normalize(query)
        
        try:
            # Exact match lookup first
            cursor = self.db.query(ScrapeSessionCursor).filter(
                ScrapeSessionCursor.user_id == user_id,
                ScrapeSessionCursor.query_hash == query_hash,
                ScrapeSessionCursor.expires_at > datetime.utcnow()
            ).first()

            if cursor:
                # Update last_accessed timestamp
                cursor.last_accessed = datetime.utcnow()
                self.db.commit()

                logger.info(
                    f"✅ Cursor hit: '{query}' (normalized: '{query_normalized}') | "
                    f"Cards: {cursor.cards_collected}, Position: {cursor.last_scroll_position}"
                )
                return cursor

            # Fuzzy match fallback - helpful for typos and small variations
            all_cursors = self.db.query(ScrapeSessionCursor).filter(
                ScrapeSessionCursor.user_id == user_id,
                ScrapeSessionCursor.expires_at > datetime.utcnow()
            ).all()

            for c in all_cursors:
                try:
                    if self.normalizer.fuzzy_match(query, c.query_original, threshold=0.85):
                        # Update last_accessed
                        c.last_accessed = datetime.utcnow()
                        self.db.commit()
                        logger.info(f"✅ Fuzzy cursor match: '{query}' → '{c.query_original}' (id={c.id})")
                        return c
                except Exception:
                    continue

            logger.info(f"❌ No cursor found for: '{query}' (normalized: '{query_normalized}')")
            return None

        except Exception as e:
            logger.error(f"Error getting cursor: {e}")
            return None
    
    def create_cursor(
        self, 
        user_id: str, 
        query: str
    ) -> ScrapeSessionCursor:
        """
        Create new cursor for a query.
        
        Args:
            user_id: User identifier
            query: Search query (will be normalized)
            
        Returns:
            New ScrapeSessionCursor instance
        """
        query_hash = self.normalizer.get_hash(query)
        query_normalized = self.normalizer.normalize(query)
        
        try:
            cursor = ScrapeSessionCursor(
                user_id=user_id,
                query_hash=query_hash,
                query_original=query,
                query_normalized=query_normalized,
                last_scroll_position=0,
                cards_collected=0,
                total_scrolls_performed=0,
                last_visible_card_count=0,
                expires_at=datetime.utcnow() + timedelta(days=self.CURSOR_TTL_DAYS)
            )
            
            self.db.add(cursor)
            self.db.commit()
            self.db.refresh(cursor)
            
            logger.info(f"📝 Created cursor for: '{query}' (normalized: '{query_normalized}')")
            return cursor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating cursor: {e}")
            raise
    
    def get_or_create_cursor(
        self, 
        user_id: str, 
        query: str
    ) -> ScrapeSessionCursor:
        """
        Get existing cursor or create new one.
        
        Convenience method that combines get_cursor and create_cursor.
        
        Args:
            user_id: User identifier
            query: Search query
            
        Returns:
            ScrapeSessionCursor (existing or new)
        """
        cursor = self.get_cursor(user_id, query)
        if cursor:
            return cursor
        return self.create_cursor(user_id, query)
    
    def update_cursor(
        self,
        user_id: str,
        query: str,
        cards_collected: int,
        last_scroll_position: int,
        last_place_id: Optional[str] = None,
        last_card_index: Optional[int] = None,
        total_scrolls: Optional[int] = None,
        visible_card_count: Optional[int] = None,
        cursor_data: Optional[Dict[str, Any]] = None
    ) -> ScrapeSessionCursor:
        """
        Update cursor with new pagination state.
        
        Called after each scrape to save resume point.
        
        Args:
            user_id: User identifier
            query: Search query
            cards_collected: Total cards collected so far
            last_scroll_position: DOM scroll height reached
            last_place_id: Last Place ID at cursor position
            last_card_index: Card index in DOM
            total_scrolls: Total scrolls performed
            visible_card_count: Cards visible when cursor saved
            cursor_data: Additional state data (JSON)
            
        Returns:
            Updated ScrapeSessionCursor
        """
        query_hash = self.normalizer.get_hash(query)
        
        try:
            cursor = self.db.query(ScrapeSessionCursor).filter(
                ScrapeSessionCursor.user_id == user_id,
                ScrapeSessionCursor.query_hash == query_hash
            ).first()
            
            if not cursor:
                cursor = self.create_cursor(user_id, query)
            
            # Update pagination state
            cursor.cards_collected = cards_collected
            cursor.last_scroll_position = last_scroll_position
            cursor.last_accessed = datetime.utcnow()
            
            # Extend TTL on update
            cursor.expires_at = datetime.utcnow() + timedelta(days=self.CURSOR_TTL_DAYS)
            
            # Optional fields
            if last_place_id:
                cursor.last_place_id = last_place_id
            if last_card_index is not None:
                cursor.last_card_index = last_card_index
            if total_scrolls is not None:
                cursor.total_scrolls_performed = total_scrolls
            if visible_card_count is not None:
                cursor.last_visible_card_count = visible_card_count
            if cursor_data is not None:
                cursor.cursor_data = cursor_data
            
            self.db.commit()
            self.db.refresh(cursor)
            
            logger.info(
                f"✅ Updated cursor: '{query}' | "
                f"Cards: {cards_collected}, Position: {last_scroll_position}"
            )
            return cursor
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating cursor: {e}")
            raise
    
    def clear_cursor(
        self, 
        user_id: str, 
        query: str
    ) -> bool:
        """
        Clear cursor if user wants to start fresh.
        
        Args:
            user_id: User identifier
            query: Search query
            
        Returns:
            True if cursor was deleted, False if not found
        """
        query_hash = self.normalizer.get_hash(query)
        
        try:
            result = self.db.query(ScrapeSessionCursor).filter(
                ScrapeSessionCursor.user_id == user_id,
                ScrapeSessionCursor.query_hash == query_hash
            ).delete()
            
            self.db.commit()
            
            if result > 0:
                logger.info(f"🗑️ Cleared cursor for: '{query}'")
            return result > 0
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing cursor: {e}")
            return False
    
    def get_user_cursors(
        self, 
        user_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all active cursors for a user.
        
        Useful for cursor management UI.
        
        Args:
            user_id: User identifier
            limit: Maximum cursors to return
            
        Returns:
            List of cursor dictionaries
        """
        try:
            cursors = self.db.query(ScrapeSessionCursor).filter(
                ScrapeSessionCursor.user_id == user_id,
                ScrapeSessionCursor.expires_at > datetime.utcnow()
            ).order_by(
                desc(ScrapeSessionCursor.last_accessed)
            ).limit(limit).all()
            
            return [cursor.to_dict() for cursor in cursors]
            
        except Exception as e:
            logger.error(f"Error getting user cursors: {e}")
            return []
    
    def cleanup_expired_cursors(self) -> int:
        """
        Clean up expired cursors.
        
        Should be called periodically (e.g., daily cron job).
        
        Returns:
            Number of cursors deleted
        """
        try:
            deleted = self.db.query(ScrapeSessionCursor).filter(
                ScrapeSessionCursor.expires_at < datetime.utcnow()
            ).delete()
            
            self.db.commit()
            
            if deleted > 0:
                logger.info(f"🧹 Cleaned up {deleted} expired cursors")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning expired cursors: {e}")
            return 0
    
    def get_cursor_summary(
        self, 
        user_id: str, 
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a summary of cursor state for API response.
        
        Args:
            user_id: User identifier
            query: Search query
            
        Returns:
            Summary dict or None
        """
        cursor = self.get_cursor(user_id, query)
        if not cursor:
            return None
        
        return {
            "has_cursor": True,
            "cards_collected": cursor.cards_collected,
            "last_scroll_position": cursor.last_scroll_position,
            "last_place_id": cursor.last_place_id[:20] + "..." if cursor.last_place_id else None,
            "last_accessed": cursor.last_accessed.isoformat() if cursor.last_accessed else None,
            "expires_at": cursor.expires_at.isoformat() if cursor.expires_at else None,
            "can_resume": cursor.cards_collected > 0
        }


# Factory function for easy imports
def get_cursor_manager(db: Session) -> CursorManager:
    """Factory function for CursorManager."""
    return CursorManager(db)
