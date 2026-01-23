"""
Scraping API endpoints for Scrappy v2.0

Main endpoints (all require authentication):
- POST /scrape - Scrape Google Maps for a query (returns scrape_id for progress tracking)
- GET /scrape/{scrape_id}/progress - Get real-time progress for a scrape
- POST /save-to-sheets - Save results to Google Sheets
- POST /send-outreach - Send SMS outreach to businesses
- GET /session-info - Get browser session pool statistics
- POST /release-session - Release user's browser session
- GET /history - Get user's scrape history
- GET /stats - Get user's dashboard stats
"""

import time
import uuid
import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from models.schemas import (
    ScrapeRequest,
    ScrapeResponse,
    ScrapeStats,
    BusinessResult,
    GoogleSheetsRequest,
    GoogleSheetsResponse,
    SMSOutreachRequest,
    SMSOutreachResponse,
    SMSSingleResult,
    ErrorResponse
)
from models.better_auth import BetterAuthUser
from services.scraper import GoogleMapsScraper
from services.google_sheets import sheets_service
from services.sms_service import sms_service
from services.browser_session_pool import browser_pool
from services.progress_tracker import (
    progress_tracker,
    create_scrape_progress,
    update_scrape_progress,
    get_scrape_progress,
    complete_scrape_progress,
    fail_scrape_progress
)
from services.history_service import get_history_service
from middleware.auth import get_current_user
from database import get_db
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Store for background scrape tasks
active_scrape_tasks: Dict[str, asyncio.Task] = {}


@router.post(
    "/scrape",
    response_model=ScrapeResponse,
    responses={
        200: {"description": "Successful scrape"},
        401: {"description": "Unauthorized - valid token required"},
        500: {"model": ErrorResponse, "description": "Scraping error"}
    }
)
async def scrape_query(
    request: ScrapeRequest,
    user: BetterAuthUser = Depends(get_current_user)  # 🔐 PROTECTED
):
    """
    Scrape Google Maps for a search query.
    
    **🔐 Requires authentication** - Include Bearer token in Authorization header.
    
    This endpoint:
    1. Searches Google Maps for the query
    2. Scrolls to load business cards
    3. Extracts details from 4-5 cards in parallel
    4. Deduplicates by Place ID
    5. Returns unique business results
    
    **Parameters:**
    - `query`: Search term (e.g., "dentists in Amritsar")
    - `target_count`: How many results to collect (default: 50)
    - `max_scrolls`: Maximum scroll attempts (default: 50)
    
    **Example Request:**
    ```json
    {
        "query": "restaurants in Amritsar",
        "target_count": 50,
        "max_scrolls": 50
    }
    ```
    """
    start_time = time.time()
    
    logger.info(f"🚀 API Request by {user.email}: Scrape for '{request.search_query}' (target: {request.target_count})")
    
    try:
        async with GoogleMapsScraper(
            max_concurrent_cards=settings.MAX_CONCURRENT_CARDS
        ) as scraper:
            results = await scraper.scrape(
                query=request.search_query,
                target_count=request.target_count,
                max_scrolls=request.max_scrolls
            )
            
            stats = scraper.get_stats()
        
        time_taken = round(time.time() - start_time, 2)
        
        # Convert results to BusinessResult models
        business_results = [
            BusinessResult(**result) for result in results
        ]
        
        logger.info(
            f"✅ API Response: {len(business_results)} results in {time_taken}s | "
            f"Scrolls: {stats.get('scrolls_performed', 0)} | "
            f"Errors: {stats.get('extraction_errors', 0)}"
        )
        
        return ScrapeResponse(
            status="success",
            query=request.search_query,
            total_collected=stats.get('cards_found', 0),
            unique_results=len(business_results),
            target_count=request.target_count,
            time_taken=time_taken,
            results=business_results,
            stats=ScrapeStats(
                cards_found=stats.get('cards_found', 0),
                cards_extracted=stats.get('cards_extracted', 0),
                extraction_errors=stats.get('extraction_errors', 0),
                scrolls_performed=stats.get('scrolls_performed', 0),
                stale_scrolls=stats.get('stale_scrolls', 0),
                dedup_stats=stats.get('dedup_stats')
            )
        )
        
    except Exception as e:
        time_taken = round(time.time() - start_time, 2)
        logger.error(f"Scrape failed after {time_taken}s: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Scraping failed: {str(e)}",
                "query": request.search_query,
                "time_taken": time_taken
            }
        )


# ============================================================================
# ASYNC SCRAPE WITH PROGRESS TRACKING
# ============================================================================

async def _run_scrape_with_progress(
    scrape_id: str,
    query: str,
    target_count: int,
    max_scrolls: int,
    user_id: str,
    user_email: str,
    seen_places: set = None
):
    """
    Background task that runs the scrape and updates progress.
    This is called by scrape_async and runs in the background.
    
    Args:
        scrape_id: Unique ID for progress tracking
        query: Search query
        target_count: Number of results to collect
        max_scrolls: Maximum scroll attempts
        user_id: User ID for history recording
        user_email: User email for logging
        seen_places: Set of Place IDs to skip (deduplication)
    """
    start_time = time.time()
    try:
        update_scrape_progress(
            scrape_id,
            status="scrolling",
            phase="Initializing browser...",
            progress_percent=2
        )
        
        async with GoogleMapsScraper(
            max_concurrent_cards=settings.MAX_CONCURRENT_CARDS
        ) as scraper:
            # Set scrape_id on the scraper for internal progress updates
            scraper._progress_scrape_id = scrape_id
            
            results = await scraper.scrape(
                query=query,
                target_count=target_count,
                max_scrolls=max_scrolls,
                seen_places=seen_places
            )
            
            stats = scraper.get_stats()
        
        time_taken = round(time.time() - start_time, 2)
        
        # Convert to BusinessResult models
        business_results = [
            BusinessResult(**result).model_dump() for result in results
        ]
        
        # Record scraped places to database for future deduplication
        # Note: We create a new DB session here since we're in a background task
        try:
            from database import SessionLocal
            db = SessionLocal()
            try:
                history_service = get_history_service(db)
                
                # Record new place IDs
                place_ids = [r.get('place_id') for r in results if r.get('place_id')]
                cids = {r.get('place_id'): r.get('cid') for r in results if r.get('place_id') and r.get('cid')}
                
                history_service.record_scraped_places(
                    user_id=user_id,
                    place_ids=place_ids,
                    query=query,
                    cids=cids
                )
                
                # Create session record
                session = history_service.create_scrape_session(
                    user_id=user_id,
                    query=query
                )
                
                # Complete the session
                history_service.complete_scrape_session(
                    session_id=str(session.id),
                    total_found=stats.get('cards_found', 0),
                    new_results=len(results),
                    skipped_duplicates=stats.get('skipped_duplicates', 0),
                    time_taken=time_taken
                )
                
                logger.info(f"📝 Recorded {len(place_ids)} places for user {user_id[:8]}...")
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to record history: {e}")
            # Don't fail the scrape if history recording fails
        
        # Mark as complete
        complete_scrape_progress(scrape_id, business_results, success=True)
        
        logger.info(f"✅ Async scrape {scrape_id} complete: {len(business_results)} results in {time_taken}s")
        
    except Exception as e:
        logger.error(f"❌ Async scrape {scrape_id} failed: {e}")
        fail_scrape_progress(scrape_id, str(e))


@router.post(
    "/scrape-async",
    responses={
        200: {"description": "Scrape started, returns scrape_id for progress tracking"},
        401: {"description": "Unauthorized - valid token required"},
    }
)
async def scrape_query_async(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start an async scrape with real-time progress tracking.
    
    **🔐 Requires authentication** - Include Bearer token in Authorization header.
    
    Returns immediately with a `scrape_id`. Use `/scrape/{scrape_id}/progress` 
    to poll for updates.
    
    **Deduplication:**
    Automatically skips businesses you've already scraped before.
    
    **Flow:**
    1. POST /scrape-async → Get scrape_id
    2. GET /scrape/{scrape_id}/progress (poll every 500ms)
    3. When status="completed", results are in the progress response
    
    **Example Response:**
    ```json
    {
        "scrape_id": "abc123",
        "status": "started",
        "message": "Scrape started. Poll /scrape/abc123/progress for updates."
    }
    ```
    """
    # Generate unique scrape ID
    scrape_id = str(uuid.uuid4())[:8]
    
    logger.info(f"🚀 Async scrape started by {user.email}: '{request.search_query}' (id: {scrape_id})")
    
    # Get user's seen places for deduplication
    try:
        history_service = get_history_service(db)
        seen_places = history_service.get_user_seen_places(str(user.id))
        logger.info(f"🔄 User has {len(seen_places)} previously scraped places")
    except Exception as e:
        logger.warning(f"Failed to get seen places: {e}")
        seen_places = set()
    
    # Create progress tracker
    create_scrape_progress(
        scrape_id=scrape_id,
        target_count=request.target_count,
        max_scrolls=request.max_scrolls
    )
    
    # Start background task
    task = asyncio.create_task(
        _run_scrape_with_progress(
            scrape_id=scrape_id,
            query=request.search_query,
            target_count=request.target_count,
            max_scrolls=request.max_scrolls,
            user_id=str(user.id),
            user_email=user.email,
            seen_places=seen_places
        )
    )
    active_scrape_tasks[scrape_id] = task
    
    return {
        "scrape_id": scrape_id,
        "status": "started",
        "query": request.search_query,
        "seen_places_count": len(seen_places),
        "target_count": request.target_count,
        "message": f"Scrape started. Poll /api/scrape/{scrape_id}/progress for updates."
    }


@router.get(
    "/scrape/{scrape_id}/progress",
    responses={
        200: {"description": "Progress data"},
        404: {"description": "Scrape not found"},
    }
)
async def get_progress(scrape_id: str):
    """
    Get real-time progress for an async scrape.
    
    **Poll this endpoint every 500ms** to get live updates.
    
    **Response Fields:**
    - `status`: "starting" | "scrolling" | "extracting" | "completed" | "failed"
    - `progress_percent`: 0-100
    - `stats`: Live statistics (cards_found, cards_extracted, etc.)
    - `preview`: First 5 extracted results
    - `sample_result`: Latest extracted business (for live preview)
    
    **When `status="completed"`:**
    The final results are available in the progress tracker.
    Call `/scrape/{scrape_id}/results` to get full results.
    """
    progress = get_scrape_progress(scrape_id)
    
    if not progress:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Scrape {scrape_id} not found"}
        )
    
    return progress


@router.get(
    "/scrape/{scrape_id}/results",
    response_model=ScrapeResponse,
    responses={
        200: {"description": "Final scrape results"},
        404: {"description": "Scrape not found"},
        425: {"description": "Scrape still in progress"},
    }
)
async def get_scrape_results(scrape_id: str):
    """
    Get final results for a completed async scrape.
    
    Only call this after progress shows `status="completed"`.
    """
    progress_data = progress_tracker.get_progress(scrape_id)
    
    if not progress_data:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Scrape {scrape_id} not found"}
        )
    
    if progress_data.status != "completed":
        raise HTTPException(
            status_code=425,  # Too Early
            detail={
                "error": "Scrape still in progress",
                "status": progress_data.status,
                "progress_percent": progress_data.progress_percent
            }
        )
    
    # Convert stored results to response
    results = progress_data.final_results or []
    business_results = [
        BusinessResult(**r) if isinstance(r, dict) else r
        for r in results
    ]
    
    return ScrapeResponse(
        status="success",
        query=progress_data.scrape_id,  # We don't store query, use ID
        total_collected=progress_data.cards_found,
        unique_results=len(business_results),
        target_count=progress_data.target_count,
        time_taken=round(time.time() - progress_data.start_time, 2),
        results=business_results,
        stats=ScrapeStats(
            cards_found=progress_data.cards_found,
            cards_extracted=progress_data.cards_extracted,
            extraction_errors=progress_data.extraction_errors,
            scrolls_performed=progress_data.scrolls_done,
            stale_scrolls=0,
            dedup_stats=None
        )
    )


@router.websocket("/ws/scrape/{scrape_id}")
async def websocket_progress(websocket: WebSocket, scrape_id: str):
    """
    WebSocket endpoint for real-time progress updates.
    
    Connect to receive push updates instead of polling.
    """
    await websocket.accept()
    logger.info(f"📡 WebSocket connected for scrape: {scrape_id}")
    
    try:
        while True:
            progress = get_scrape_progress(scrape_id)
            
            if not progress:
                await websocket.send_json({"error": "Scrape not found"})
                break
            
            await websocket.send_json(progress)
            
            if progress.get("status") in ["completed", "failed"]:
                break
            
            await asyncio.sleep(0.5)  # Push every 500ms
            
    except WebSocketDisconnect:
        logger.info(f"📡 WebSocket disconnected for scrape: {scrape_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@router.post(
    "/save-to-sheets",
    response_model=GoogleSheetsResponse,
    responses={
        200: {"description": "Successfully saved to sheets"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"description": "Unauthorized - valid token required"},
        500: {"model": ErrorResponse, "description": "Google Sheets error"}
    }
)
async def save_to_sheets(
    request: GoogleSheetsRequest,
    user: BetterAuthUser = Depends(get_current_user)  # 🔐 PROTECTED
):
    """
    Save scraping results to Google Sheets.
    
    **🔐 Requires authentication** - Include Bearer token in Authorization header.
    
    This endpoint appends the provided results to a Google Spreadsheet.
    The spreadsheet must be shared with the service account email.
    
    **Prerequisites:**
    1. Set `GOOGLE_SHEETS_CREDENTIALS_JSON` in environment
    2. Share the spreadsheet with the service account email
    
    **Parameters:**
    - `results`: List of BusinessResult objects to save
    - `spreadsheet_id`: ID of the Google Spreadsheet
    - `sheet_name`: Name of the sheet to append to (default: "Scrappy Results")
    
    **Example Request:**
    ```json
    {
        "results": [...],
        "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        "sheet_name": "Scrappy Results"
    }
    ```
    """
    logger.info(f"📊 Save to Sheets by {user.email}: {len(request.results)} results")
    if not request.results:
        return GoogleSheetsResponse(
            success=True,
            rows_added=0,
            message="No results to save"
        )
    
    try:
        # Convert Pydantic models to dicts
        results_dicts = [r.model_dump() for r in request.results]
        
        # Use provided ID or fallback to settings
        target_spreadsheet_id = request.spreadsheet_id or settings.SPREADSHEET_ID
        
        if not target_spreadsheet_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "Spreadsheet ID not provided",
                    "detail": "Please provide a spreadsheet_id in the request or configure SPREADSHEET_ID in backend settings."
                }
            )

        result = await sheets_service.append_results(
            spreadsheet_id=target_spreadsheet_id,
            sheet_name=request.sheet_name,
            results=results_dicts
        )
        
        if result['success']:
            logger.info(
                f"Saved {result['rows_added']} rows to "
                f"{request.spreadsheet_id}/{request.sheet_name}"
            )
        
        return GoogleSheetsResponse(**result)
        
    except ValueError as e:
        logger.error(f"Value error: {e}")
        # This catches our custom credential validation errors
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(e).split('\n')[0],  # First line of the error
                "detail": str(e)
            }
        )
    except FileNotFoundError as e:
        logger.error(f"Credentials file not found: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Google Sheets credentials not found",
                "detail": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Google Sheets error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to save to Google Sheets: {str(e)}"
            }
        )


@router.post(
    "/send-outreach",
    response_model=SMSOutreachResponse,
    responses={
        200: {"description": "Outreach sent"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"description": "Unauthorized - valid token required"},
        500: {"model": ErrorResponse, "description": "SMS service error"}
    }
)
async def send_outreach(
    request: SMSOutreachRequest,
    user: BetterAuthUser = Depends(get_current_user)  # 🔐 PROTECTED
):
    """
    Send SMS outreach messages to businesses.
    
    **🔐 Requires authentication** - Include Bearer token in Authorization header.
    
    This endpoint sends personalized SMS messages to all businesses
    in the provided results list that have phone numbers.
    
    **Template Variables:**
    - `{name}`: Business name
    - `{phone}`: Business phone
    - `{address}`: Business address
    - `{website}`: Business website
    - `{rating}`: Business rating
    - `{category}`: Business category
    
    **Providers:**
    - `twilio`: International SMS (requires TWILIO_* env vars)
    - `fast2sms`: India-focused SMS (requires FAST2SMS_* env vars)
    
    **Example Request:**
    ```json
    {
        "results": [...],
        "message_template": "Hey {name}! Check out our services at example.com",
        "provider": "twilio"
    }
    ```
    """
    if not request.results:
        return SMSOutreachResponse(
            total=0,
            success=0,
            failed=0,
            skipped=0,
            provider=request.provider,
            results=[]
        )
    
    try:
        # Convert Pydantic models to dicts
        results_dicts = [r.model_dump() for r in request.results]
        
        result = await sms_service.send_sms_batch(
            results=results_dicts,
            message_template=request.message_template,
            provider=request.provider
        )
        
        # Convert individual results to Pydantic models
        sms_results = [
            SMSSingleResult(**r) for r in result['results']
        ]
        
        logger.info(
            f"SMS outreach: {result['success']} sent, "
            f"{result['failed']} failed via {request.provider}"
        )
        
        return SMSOutreachResponse(
            total=result['total'],
            success=result['success'],
            failed=result['failed'],
            skipped=result['skipped'],
            provider=result['provider'],
            results=sms_results
        )
        
    except Exception as e:
        logger.error(f"SMS outreach error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"SMS outreach failed: {str(e)}"
            }
        )


@router.post("/scrape-and-save")
async def scrape_and_save(
    query: str,
    spreadsheet_id: str,
    sheet_name: str = "Scrappy Results",
    target_count: int = 50,
    max_scrolls: int = 50
):
    """
    Scrape Google Maps and save results directly to Google Sheets.
    
    This is a convenience endpoint that combines scraping and saving
    in a single operation.
    
    **Parameters:**
    - `query`: Search term
    - `spreadsheet_id`: Google Spreadsheet ID
    - `sheet_name`: Sheet name (default: "Scrappy Results")
    - `target_count`: Number of results to collect
    - `max_scrolls`: Maximum scroll attempts
    """
    start_time = time.time()
    
    try:
        # Step 1: Scrape
        async with GoogleMapsScraper(
            max_concurrent_cards=settings.MAX_CONCURRENT_CARDS
        ) as scraper:
            results = await scraper.scrape(
                query=query,
                target_count=target_count,
                max_scrolls=max_scrolls
            )
            stats = scraper.get_stats()
        
        scrape_time = round(time.time() - start_time, 2)
        
        # Step 2: Save to sheets
        save_result = await sheets_service.append_results(
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name,
            results=results
        )
        
        total_time = round(time.time() - start_time, 2)
        
        return {
            "status": "success",
            "query": query,
            "scrape": {
                "unique_results": len(results),
                "total_collected": stats.get('cards_found', 0),
                "time_taken": scrape_time
            },
            "sheets": {
                "success": save_result['success'],
                "rows_added": save_result['rows_added'],
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name
            },
            "total_time": total_time
        }
        
    except Exception as e:
        logger.error(f"Scrape and save error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e)
            }
        )


@router.get("/sample-results")
async def sample_results():
    """
    Get sample business results for testing.
    
    Returns sample data that can be used to test the
    save-to-sheets and send-outreach endpoints.
    """
    return {
        "results": [
            {
                "place_id": "0x890cb024fe77e7b6",
                "cid": "12345678901234567890",
                "name": "Sample Pizza Place",
                "address": "123 Main St, Amritsar, Punjab",
                "phone": "+91-9876543210",
                "website": "https://example.com",
                "rating": 4.5,
                "reviews_count": 342,
                "category": "Restaurant",
                "hours": "10:00 AM - 10:00 PM",
                "is_claimed": True
            },
            {
                "place_id": "0x890cb024fe77e7b7",
                "name": "Sample Dental Clinic",
                "address": "456 Oak St, Amritsar, Punjab",
                "phone": "+91-9876543211",
                "rating": 4.8,
                "reviews_count": 128,
                "category": "Dentist",
                "is_claimed": False
            }
        ],
        "message": "Use these sample results to test /api/save-to-sheets and /api/send-outreach"
    }


# ============================================
# Browser Session Management Endpoints
# ============================================

@router.get("/session-info")
async def get_session_info(
    user: BetterAuthUser = Depends(get_current_user)
):
    """
    Get browser session pool statistics.
    
    **🔐 Requires authentication**
    
    Returns information about active browser sessions including:
    - Total active sessions
    - Available slots
    - Session details per user (idle time, age, scrape count)
    
    Useful for monitoring system health and debugging.
    """
    return browser_pool.get_session_info()


@router.post("/release-session")
async def release_my_session(
    user: BetterAuthUser = Depends(get_current_user)
):
    """
    Release user's browser session.
    
    **🔐 Requires authentication**
    
    Manually closes the user's browser session to free up resources.
    Sessions are automatically cleaned up after 30 minutes of inactivity,
    but you can use this endpoint to release immediately.
    
    Returns:
        Success message
    """
    await browser_pool.release_session(str(user.id))
    return {
        "success": True,
        "message": "Browser session released"
    }


@router.post("/reset-session")
async def reset_my_session(
    user: BetterAuthUser = Depends(get_current_user)
):
    """
    Reset user's browser session.
    
    **🔐 Requires authentication**
    
    Forces a complete reset of the user's browser session.
    Useful if the session becomes corrupted or stuck.
    
    Returns:
        Success message with new session info
    """
    await browser_pool.reset_session(str(user.id))
    return {
        "success": True,
        "message": "Browser session reset successfully"
    }


# ============================================================================
# HISTORY & DEDUPLICATION ENDPOINTS
# ============================================================================

@router.get("/history")
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's scrape history.
    
    **🔐 Requires authentication**
    
    Returns a list of past scraping sessions with:
    - Query performed
    - Results count (new vs duplicates skipped)
    - Google Sheets links
    - Time taken
    - Status (completed/failed)
    
    **Pagination:**
    - `limit`: Number of results (default 20, max 100)
    - `offset`: Skip this many records (for pagination)
    """
    try:
        history_service = get_history_service(db)
        
        history = history_service.get_user_history(
            user_id=str(user.id),
            limit=limit,
            offset=offset
        )
        
        total = history_service.get_history_count(str(user.id))
        
        return {
            "success": True,
            "history": history,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(history) < total
        }
        
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to fetch history", "message": str(e)}
        )


@router.get("/stats")
async def get_user_stats(
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's dashboard statistics.
    
    **🔐 Requires authentication**
    
    Returns:
    - Total unique businesses scraped
    - Total scraping sessions
    - Results collected
    - Duplicates skipped (time saved)
    - Deduplication efficiency percentage
    - Recent scrapes
    """
    try:
        history_service = get_history_service(db)
        stats = history_service.get_user_stats(str(user.id))
        
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to fetch stats", "message": str(e)}
        )


@router.get("/seen-places")
async def get_seen_places_count(
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get count of places user has previously scraped.
    
    **🔐 Requires authentication**
    
    Useful for showing deduplication status before starting a new scrape.
    """
    try:
        history_service = get_history_service(db)
        count = history_service.get_user_unique_count(str(user.id))
        
        return {
            "success": True,
            "seen_places_count": count,
            "message": f"You have {count} businesses in your deduplication database"
        }
        
    except Exception as e:
        logger.error(f"Error fetching seen places: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to fetch seen places", "message": str(e)}
        )


@router.post("/user-sheet")
async def set_user_sheet(
    sheet_id: str,
    sheet_name: Optional[str] = None,
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set user's default Google Sheet for results.
    
    **🔐 Requires authentication**
    
    When a user sets their default sheet, all future scrapes will
    automatically export to this sheet.
    """
    try:
        history_service = get_history_service(db)
        success = history_service.set_user_google_sheet(
            user_id=str(user.id),
            sheet_id=sheet_id,
            sheet_name=sheet_name
        )
        
        if success:
            return {
                "success": True,
                "message": "Default Google Sheet set successfully",
                "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={"error": "Failed to set sheet"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting user sheet: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to set sheet", "message": str(e)}
        )


@router.get("/user-sheet")
async def get_user_sheet(
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's default Google Sheet.
    
    **🔐 Requires authentication**
    """
    try:
        history_service = get_history_service(db)
        sheet = history_service.get_user_google_sheet(str(user.id))
        
        return {
            "success": True,
            "sheet": sheet
        }
        
    except Exception as e:
        logger.error(f"Error getting user sheet: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to get sheet", "message": str(e)}
        )
