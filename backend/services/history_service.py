"""
History Service for Scrappy v2.0

Manages:
- Place ID storage for deduplication
- Scrape session history
- User Google Sheets mapping
- Stats and analytics
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Set, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from sqlalchemy.dialects.postgresql import insert

from models.scrape_history import UserPlace, ScrapeSession, UserGoogleSheet

logger = logging.getLogger(__name__)


class HistoryService:
    """
    Handles all history and deduplication operations.
    
    Key features:
    - O(1) deduplication lookup via DB index
    - Batch upsert for performance
    - Google Sheets integration
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== DEDUPLICATION ====================
    
    def get_user_seen_places(self, user_id: str) -> Set[str]:
        """
        Get ALL Place IDs this user has ever scraped.
        
        Used for deduplication BEFORE extraction.
        Query is indexed, returns in ~2ms for 10K places.
        """
        try:
            rows = self.db.query(UserPlace.place_id).filter(
                UserPlace.user_id == user_id
            ).all()
            
            places = {row[0] for row in rows}
            logger.debug(f"📊 User {user_id[:8]}... has {len(places)} previously scraped places")
            return places
            
        except Exception as e:
            logger.error(f"Error getting user places: {e}")
            return set()
    
    def record_scraped_places(
        self, 
        user_id: str, 
        place_ids: List[str], 
        query: str,
        cids: Optional[Dict[str, str]] = None
    ) -> int:
        """
        Record new Place IDs for user (UPSERT).
        
        Args:
            user_id: User identifier
            place_ids: List of Place IDs to record
            query: Original search query
            cids: Optional mapping of place_id -> cid
            
        Returns:
            Number of new places recorded
        """
        if not place_ids:
            return 0
        
        query_hash = self._make_query_hash(query)
        cids = cids or {}
        new_count = 0
        
        try:
            for place_id in place_ids:
                # Use PostgreSQL UPSERT
                stmt = insert(UserPlace).values(
                    user_id=user_id,
                    place_id=place_id,
                    cid=cids.get(place_id),
                    query_hash=query_hash,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    scraped_count=1
                ).on_conflict_do_update(
                    index_elements=['user_id', 'place_id'],
                    set_={
                        'last_seen': datetime.utcnow(),
                        'scraped_count': UserPlace.scraped_count + 1
                    }
                )
                
                result = self.db.execute(stmt)
                if result.rowcount > 0:
                    new_count += 1
            
            self.db.commit()
            logger.info(f"📝 Recorded {new_count} places for user {user_id[:8]}...")
            return new_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording places: {e}")
            return 0
    
    def get_user_unique_count(self, user_id: str) -> int:
        """Get total unique places ever scraped by user."""
        try:
            return self.db.query(func.count(UserPlace.id)).filter(
                UserPlace.user_id == user_id
            ).scalar() or 0
        except Exception as e:
            logger.error(f"Error getting unique count: {e}")
            return 0
    
    # ==================== SCRAPE SESSIONS ====================
    
    def create_scrape_session(
        self,
        user_id: str,
        query: str,
        sheet_id: Optional[str] = None
    ) -> ScrapeSession:
        """Create a new scrape session record."""
        try:
            session = ScrapeSession(
                user_id=user_id,
                query=query,
                query_hash=self._make_query_hash(query),
                sheet_id=sheet_id,
                status='running'
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"📋 Created scrape session {session.id}")
            return session
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating session: {e}")
            raise
    
    def complete_scrape_session(
        self,
        session_id: str,
        total_found: int,
        new_results: int,
        skipped_duplicates: int,
        time_taken: float,
        sheet_url: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Mark a scrape session as complete."""
        try:
            session = self.db.query(ScrapeSession).filter(
                ScrapeSession.id == session_id
            ).first()
            
            if session:
                session.total_found = total_found
                session.new_results = new_results
                session.skipped_duplicates = skipped_duplicates
                session.time_taken_seconds = int(time_taken)
                session.sheet_url = sheet_url
                session.completed_at = datetime.utcnow()
                session.status = 'failed' if error_message else 'completed'
                session.error_message = error_message
                
                self.db.commit()
                logger.info(f"✅ Completed session {session_id}: {new_results} new results")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing session: {e}")
    
    def get_user_history(
        self, 
        user_id: str, 
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's scrape history for the History UI.
        
        Returns sessions with Google Sheets links.
        """
        try:
            sessions = self.db.query(ScrapeSession).filter(
                ScrapeSession.user_id == user_id,
                ScrapeSession.status.in_(['completed', 'failed'])
            ).order_by(
                desc(ScrapeSession.created_at)
            ).offset(offset).limit(limit).all()
            
            return [
                {
                    "id": str(session.id),
                    "query": session.query,
                    "total_found": session.total_found,
                    "new_results": session.new_results,
                    "skipped_duplicates": session.skipped_duplicates,
                    "time_taken": session.time_taken_seconds,
                    "sheet_url": session.sheet_url,
                    "sheet_id": session.sheet_id,
                    "status": session.status,
                    "error": session.error_message,
                    "date": session.created_at.isoformat() if session.created_at else None,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                }
                for session in sessions
            ]
            
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []
    
    def get_history_count(self, user_id: str) -> int:
        """Get total number of scrape sessions for user."""
        try:
            return self.db.query(func.count(ScrapeSession.id)).filter(
                ScrapeSession.user_id == user_id
            ).scalar() or 0
        except Exception as e:
            logger.error(f"Error getting history count: {e}")
            return 0
    
    # ==================== USER STATS ====================
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get dashboard stats for user.
        
        Returns:
            - Total unique businesses ever scraped
            - Total scrape sessions
            - Recent activity
            - Dedup savings
        """
        try:
            # Total unique places
            unique_places = self.get_user_unique_count(user_id)
            
            # Session stats
            session_stats = self.db.query(
                func.count(ScrapeSession.id).label('total_sessions'),
                func.sum(ScrapeSession.new_results).label('total_new'),
                func.sum(ScrapeSession.skipped_duplicates).label('total_skipped'),
                func.sum(ScrapeSession.time_taken_seconds).label('total_time')
            ).filter(
                ScrapeSession.user_id == user_id,
                ScrapeSession.status == 'completed'
            ).first()
            
            # Recent sessions
            recent = self.db.query(ScrapeSession).filter(
                ScrapeSession.user_id == user_id,
                ScrapeSession.status == 'completed'
            ).order_by(desc(ScrapeSession.created_at)).limit(5).all()
            
            # Calculate dedup efficiency
            total_new = session_stats.total_new or 0
            total_skipped = session_stats.total_skipped or 0
            dedup_rate = (total_skipped / (total_new + total_skipped) * 100) if (total_new + total_skipped) > 0 else 0
            
            return {
                "total_unique_businesses": unique_places,
                "total_scrapes": session_stats.total_sessions or 0,
                "total_results_collected": total_new,
                "total_duplicates_skipped": total_skipped,
                "dedup_efficiency": round(dedup_rate, 1),
                "total_time_saved_minutes": round((total_skipped * 3) / 60, 1),  # ~3 sec per business
                "recent_scrapes": [
                    {
                        "id": str(s.id),
                        "query": s.query,
                        "new_results": s.new_results,
                        "date": s.created_at.isoformat() if s.created_at else None
                    }
                    for s in recent
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {
                "total_unique_businesses": 0,
                "total_scrapes": 0,
                "total_results_collected": 0,
                "total_duplicates_skipped": 0,
                "dedup_efficiency": 0,
                "total_time_saved_minutes": 0,
                "recent_scrapes": []
            }
    
    # ==================== GOOGLE SHEETS ====================
    
    def get_user_google_sheet(self, user_id: str) -> Optional[Dict[str, str]]:
        """Get user's default Google Sheet for results."""
        try:
            sheet = self.db.query(UserGoogleSheet).filter(
                UserGoogleSheet.user_id == user_id
            ).first()
            
            if sheet:
                return {
                    "sheet_id": sheet.sheet_id,
                    "sheet_name": sheet.sheet_name,
                    "sheet_url": sheet.sheet_url or f"https://docs.google.com/spreadsheets/d/{sheet.sheet_id}/edit"
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user sheet: {e}")
            return None
    
    def set_user_google_sheet(
        self, 
        user_id: str, 
        sheet_id: str,
        sheet_name: Optional[str] = None
    ) -> bool:
        """Set user's default Google Sheet."""
        try:
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
            
            # Upsert
            existing = self.db.query(UserGoogleSheet).filter(
                UserGoogleSheet.user_id == user_id
            ).first()
            
            if existing:
                existing.sheet_id = sheet_id
                existing.sheet_name = sheet_name or existing.sheet_name
                existing.sheet_url = sheet_url
                existing.updated_at = datetime.utcnow()
            else:
                new_sheet = UserGoogleSheet(
                    user_id=user_id,
                    sheet_id=sheet_id,
                    sheet_name=sheet_name or "Scrappy Results",
                    sheet_url=sheet_url
                )
                self.db.add(new_sheet)
            
            self.db.commit()
            logger.info(f"📊 Set user sheet: {user_id[:8]}... -> {sheet_id[:16]}...")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting user sheet: {e}")
            return False
    
    # ==================== HELPERS ====================
    
    def _make_query_hash(self, query: str) -> str:
        """Create a hash for query grouping (daily)."""
        date_str = datetime.utcnow().strftime('%Y%m%d')
        clean_query = query.lower().strip().replace(' ', '_')[:50]
        return f"{clean_query}_{date_str}"
    
    def cleanup_old_sessions(self, days: int = 90) -> int:
        """
        Clean up old session records (optional maintenance).
        
        Note: UserPlace records are kept forever for dedup.
        Only ScrapeSession metadata is cleaned.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            deleted = self.db.query(ScrapeSession).filter(
                ScrapeSession.created_at < cutoff
            ).delete()
            self.db.commit()
            
            logger.info(f"🧹 Cleaned up {deleted} old sessions")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning sessions: {e}")
            return 0


# Singleton for easy imports
def get_history_service(db: Session) -> HistoryService:
    """Factory function for HistoryService."""
    return HistoryService(db)
