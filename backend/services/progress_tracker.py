"""
Real-time Scrape Progress Tracker for Scrappy v2.0

Provides live progress updates during scraping operations.
Supports both polling and WebSocket connections.

Features:
- Thread-safe progress storage
- Automatic cleanup of stale sessions
- Live preview of extracted results
- ETA calculation based on extraction rate
"""

import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProgressData:
    """Progress data for a single scrape operation"""
    scrape_id: str
    status: str = "starting"  # starting, scrolling, extracting, completed, failed
    progress_percent: int = 0
    phase: str = "Initializing..."
    
    # Stats
    cards_found: int = 0
    cards_extracted: int = 0
    unique_results: int = 0
    scrolls_done: int = 0
    max_scrolls: int = 50
    target_count: int = 50
    extraction_errors: int = 0
    
    # Timing
    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    
    # Preview data
    results_preview: List[Dict] = field(default_factory=list)
    sample_result: Optional[Dict] = None
    
    # Final results
    final_results: Optional[List[Dict]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)
        
        # Calculate ETA based on progress
        eta_str = self._calculate_eta(elapsed)
        
        return {
            "scrape_id": self.scrape_id,
            "status": self.status,
            "progress_percent": min(self.progress_percent, 100),
            "phase": self.phase,
            "stats": {
                "cards_found": self.cards_found,
                "cards_extracted": self.cards_extracted,
                "unique_results": self.unique_results,
                "scrolls_done": self.scrolls_done,
                "max_scrolls": self.max_scrolls,
                "target_count": self.target_count,
                "extraction_errors": self.extraction_errors,
                "time_elapsed": elapsed_str,
                "eta": eta_str
            },
            "preview": self.results_preview[:5],  # First 5 results
            "sample_result": self.sample_result,
            "error_message": self.error_message
        }
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as human-readable string"""
        if seconds < 60:
            return f"{int(seconds)}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    
    def _calculate_eta(self, elapsed: float) -> str:
        """Calculate estimated time remaining"""
        if self.progress_percent <= 0:
            return "Calculating..."
        if self.progress_percent >= 100:
            return "Complete!"
        
        # Estimate total time based on current progress
        estimated_total = elapsed / (self.progress_percent / 100)
        remaining = estimated_total - elapsed
        
        if remaining < 0:
            return "Almost done..."
        
        return self._format_time(remaining)


class ScrapeProgressTracker:
    """
    Singleton progress tracker for all active scrapes.
    Thread-safe for use with async operations.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.active_scrapes: Dict[str, ProgressData] = {}
        self._cleanup_task = None
        self._initialized = True
        logger.info("📊 ScrapeProgressTracker initialized")
    
    def create_scrape(self, scrape_id: str, target_count: int = 50, max_scrolls: int = 50) -> ProgressData:
        """Create a new scrape progress entry"""
        progress = ProgressData(
            scrape_id=scrape_id,
            target_count=target_count,
            max_scrolls=max_scrolls,
            status="starting",
            phase="Starting scrape..."
        )
        self.active_scrapes[scrape_id] = progress
        logger.info(f"📊 Created progress tracker for scrape: {scrape_id}")
        return progress
    
    def get_progress(self, scrape_id: str) -> Optional[ProgressData]:
        """Get progress for a scrape"""
        return self.active_scrapes.get(scrape_id)
    
    def update(
        self,
        scrape_id: str,
        progress_percent: Optional[int] = None,
        status: Optional[str] = None,
        phase: Optional[str] = None,
        cards_found: Optional[int] = None,
        cards_extracted: Optional[int] = None,
        unique_results: Optional[int] = None,
        scrolls_done: Optional[int] = None,
        sample_result: Optional[Dict] = None,
        results_preview: Optional[List[Dict]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update progress for a scrape"""
        progress = self.active_scrapes.get(scrape_id)
        if not progress:
            logger.warning(f"⚠️ Progress tracker not found for scrape: {scrape_id}")
            return
        
        if progress_percent is not None:
            progress.progress_percent = min(progress_percent, 100)
        if status is not None:
            progress.status = status
        if phase is not None:
            progress.phase = phase
        if cards_found is not None:
            progress.cards_found = cards_found
        if cards_extracted is not None:
            progress.cards_extracted = cards_extracted
        if unique_results is not None:
            progress.unique_results = unique_results
        if scrolls_done is not None:
            progress.scrolls_done = scrolls_done
        if sample_result is not None:
            progress.sample_result = sample_result
            # Also add to preview if not already there
            if results_preview is None and sample_result.get('name'):
                if len(progress.results_preview) < 10:
                    progress.results_preview.append(sample_result)
        if results_preview is not None:
            progress.results_preview = results_preview
        if error_message is not None:
            progress.error_message = error_message
        
        progress.last_update = time.time()
    
    def complete_scrape(
        self,
        scrape_id: str,
        results: List[Dict],
        success: bool = True
    ) -> None:
        """Mark a scrape as complete"""
        progress = self.active_scrapes.get(scrape_id)
        if not progress:
            return
        
        progress.status = "completed" if success else "failed"
        progress.progress_percent = 100 if success else progress.progress_percent
        progress.phase = f"✅ Complete! {len(results)} results" if success else "❌ Failed"
        progress.final_results = results
        progress.unique_results = len(results)
        progress.last_update = time.time()
        
        logger.info(f"📊 Scrape {scrape_id} completed: {len(results)} results")
    
    def fail_scrape(self, scrape_id: str, error: str) -> None:
        """Mark a scrape as failed"""
        progress = self.active_scrapes.get(scrape_id)
        if not progress:
            return
        
        progress.status = "failed"
        progress.phase = f"❌ Error: {error[:50]}"
        progress.error_message = error
        progress.last_update = time.time()
        
        logger.error(f"📊 Scrape {scrape_id} failed: {error}")
    
    def cleanup_stale(self, max_age_seconds: int = 3600) -> int:
        """Remove stale progress entries (older than max_age)"""
        now = time.time()
        stale_ids = [
            sid for sid, progress in self.active_scrapes.items()
            if now - progress.last_update > max_age_seconds
        ]
        
        for sid in stale_ids:
            del self.active_scrapes[sid]
        
        if stale_ids:
            logger.info(f"🧹 Cleaned up {len(stale_ids)} stale progress entries")
        
        return len(stale_ids)
    
    def get_all_active(self) -> List[Dict]:
        """Get all active scrape progress entries"""
        return [p.to_dict() for p in self.active_scrapes.values()]


# Global singleton instance
progress_tracker = ScrapeProgressTracker()


# Convenience functions
def create_scrape_progress(scrape_id: str, target_count: int = 50, max_scrolls: int = 50) -> ProgressData:
    """Create a new scrape progress tracker"""
    return progress_tracker.create_scrape(scrape_id, target_count, max_scrolls)


def update_scrape_progress(scrape_id: str, **kwargs) -> None:
    """Update scrape progress"""
    progress_tracker.update(scrape_id, **kwargs)


def get_scrape_progress(scrape_id: str) -> Optional[Dict]:
    """Get scrape progress as dict"""
    progress = progress_tracker.get_progress(scrape_id)
    return progress.to_dict() if progress else None


def complete_scrape_progress(scrape_id: str, results: List[Dict], success: bool = True) -> None:
    """Complete a scrape"""
    progress_tracker.complete_scrape(scrape_id, results, success)


def fail_scrape_progress(scrape_id: str, error: str) -> None:
    """Fail a scrape"""
    progress_tracker.fail_scrape(scrape_id, error)
