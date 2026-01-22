"""
Google Integration Routes for Scrappy v2.0

API endpoints for Google OAuth 2.0 flow and Google Sheets operations.
Enables per-user Google Sheets integration for saving scraped leads.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel
import secrets
import logging

from database import get_db
from middleware.auth import get_current_user
from models.better_auth import BetterAuthUser
from services.google_oauth_service import get_google_oauth_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# In-memory OAuth state storage
# NOTE: Use Redis in production for multi-instance support
# ============================================
oauth_states: dict = {}


def cleanup_expired_states():
    """Remove OAuth states older than 10 minutes"""
    now = datetime.utcnow()
    expired = [
        state for state, data in oauth_states.items()
        if (now - datetime.fromisoformat(data['timestamp'])).total_seconds() > 600
    ]
    for state in expired:
        del oauth_states[state]


# ============================================
# Request/Response Models
# ============================================

class GoogleAuthURLResponse(BaseModel):
    """Response containing Google OAuth authorization URL"""
    authorization_url: str
    state: str  # For CSRF verification


class GoogleCallbackRequest(BaseModel):
    """Request body for OAuth callback"""
    code: str
    state: str


class IntegrationStatusResponse(BaseModel):
    """Response containing integration status"""
    connected: bool
    email: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SaveToSheetsRequest(BaseModel):
    """Request to save data to Google Sheets"""
    spreadsheet_id: Optional[str] = None  # If None, create new spreadsheet
    sheet_name: str = "Scrappy Results"
    data: List[List[Any]]  # 2D array of data rows


class SaveToSheetsResponse(BaseModel):
    """Response after saving to Google Sheets"""
    success: bool
    spreadsheet_id: str
    spreadsheet_url: str
    rows_added: int


class MessageResponse(BaseModel):
    """Generic success/error response"""
    success: bool
    message: str
    email: Optional[str] = None


# ============================================
# Endpoints
# ============================================

@router.get("/authorize", response_model=GoogleAuthURLResponse)
async def authorize_google_sheets(
    current_user: BetterAuthUser = Depends(get_current_user)
):
    """
    Step 1: Generate Google OAuth authorization URL.
    
    User should be redirected to this URL to authorize Google Sheets access.
    
    Returns:
        Authorization URL and state token for CSRF protection
    """
    google_service = get_google_oauth_service()
    
    try:
        # Generate CSRF state token
        state = secrets.token_urlsafe(32)
        
        # Store state with user_id for callback verification
        cleanup_expired_states()
        oauth_states[state] = {
            'user_id': str(current_user.id),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Get authorization URL
        auth_url, _ = google_service.get_authorization_url(state)
        
        logger.info(f"Generated OAuth URL for user {current_user.email}")
        return {
            "authorization_url": auth_url,
            "state": state
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to generate OAuth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.post("/callback", response_model=MessageResponse)
async def google_oauth_callback(
    request: GoogleCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Step 2: Handle OAuth callback with authorization code.
    
    This endpoint is called after user authorizes the app on Google's consent screen.
    Exchanges the authorization code for tokens and stores them encrypted.
    
    Args:
        code: Authorization code from Google
        state: CSRF state token for verification
        
    Returns:
        Success message with connected Google email
    """
    google_service = get_google_oauth_service()
    
    # Verify state (CSRF protection)
    state_data = oauth_states.get(request.state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state token. Please try connecting again."
        )
    
    user_id = state_data['user_id']
    
    # Clean up used state
    del oauth_states[request.state]
    
    try:
        # Exchange code for tokens
        credentials = google_service.exchange_code_for_tokens(request.code)
        
        # Get user's Google email for display
        user_info = google_service.get_user_info(credentials['access_token'])
        google_email = user_info.get('email', 'Unknown')
        google_name = user_info.get('name', '')
        
        # Save integration with encrypted tokens
        google_service.save_user_integration(
            db=db,
            user_id=user_id,
            credentials=credentials,
            metadata={
                'google_email': google_email,
                'google_name': google_name,
                'picture': user_info.get('picture'),
                'connected_at': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"User {user_id} connected Google Sheets ({google_email})")
        
        return {
            "success": True,
            "message": "Google Sheets connected successfully!",
            "email": google_email
        }
        
    except Exception as e:
        logger.error(f"OAuth callback failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete Google authorization: {str(e)}"
        )


@router.get("/status", response_model=IntegrationStatusResponse)
async def get_integration_status(
    current_user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has Google Sheets integration connected.
    
    Returns:
        Integration status including connected Google email
    """
    google_service = get_google_oauth_service()
    
    integration = google_service.get_user_integration(db, str(current_user.id))
    
    if not integration:
        return {"connected": False}
    
    # Verify we can get a valid access token (decryption works)
    access_token = google_service.get_valid_access_token(db, str(current_user.id))
    if not access_token:
        # Credentials are corrupted or expired - user needs to reconnect
        logger.warning(f"User {current_user.email} has corrupted/expired Google credentials - needs to reconnect")
        return {
            "connected": False,
            "error": "Your Google connection has expired or is corrupted. Please disconnect and reconnect."
        }
    
    metadata = integration.integration_metadata or {}
    
    return {
        "connected": True,
        "email": metadata.get('google_email'),
        "created_at": integration.created_at.isoformat() if integration.created_at else None,
        "updated_at": integration.updated_at.isoformat() if integration.updated_at else None
    }


@router.post("/save-to-sheet", response_model=SaveToSheetsResponse)
async def save_to_google_sheets(
    request: SaveToSheetsRequest,
    current_user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save scraped data to user's Google Sheet.
    
    If spreadsheet_id is not provided, a new spreadsheet will be created.
    Data is appended to existing rows (doesn't overwrite).
    
    Args:
        spreadsheet_id: Existing sheet ID (optional - creates new if not provided)
        sheet_name: Name of the sheet tab (default: "Scrappy Results")
        data: 2D array of data rows to save
        
    Returns:
        Spreadsheet ID, URL, and number of rows added
    """
    google_service = get_google_oauth_service()
    
    # Get valid access token (auto-refreshes if needed)
    access_token = google_service.get_valid_access_token(db, str(current_user.id))
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Sheets not connected. Please connect your Google account first."
        )
    
    try:
        spreadsheet_id = request.spreadsheet_id
        spreadsheet_url = None
        
        # Create new spreadsheet if not provided
        if not spreadsheet_id:
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            sheet_info = google_service.create_spreadsheet(
                access_token,
                title=f"Scrappy Results - {timestamp}",
                sheet_name=request.sheet_name  # Create with the correct sheet name
            )
            spreadsheet_id = sheet_info['spreadsheetId']
            spreadsheet_url = sheet_info.get('spreadsheetUrl', f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            
            # Add headers for new spreadsheet
            headers = [[
                "Name", "Address", "Phone", "Website", 
                "Rating", "Reviews", "Category", "Place ID",
                "Latitude", "Longitude", "Scraped At"
            ]]
            google_service.write_to_sheet(
                access_token,
                spreadsheet_id,
                f"'{request.sheet_name}'!A1:K1",
                headers
            )
        else:
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        
        # Append data rows
        if request.data and len(request.data) > 0:
            google_service.append_to_sheet(
                access_token,
                spreadsheet_id,
                f"'{request.sheet_name}'!A:K",
                request.data
            )
        
        logger.info(f"Saved {len(request.data)} rows to sheet {spreadsheet_id} for user {current_user.email}")
        
        return {
            "success": True,
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": spreadsheet_url,
            "rows_added": len(request.data)
        }
        
    except Exception as e:
        logger.error(f"Failed to save to sheets for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save to Google Sheets: {str(e)}"
        )


@router.delete("/disconnect", response_model=MessageResponse)
async def disconnect_google_sheets(
    current_user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect user's Google Sheets integration.
    
    This removes stored OAuth tokens and deactivates the integration.
    User will need to re-authorize to use Google Sheets again.
    
    Returns:
        Success message
    """
    google_service = get_google_oauth_service()
    
    disconnected = google_service.disconnect_integration(db, str(current_user.id))
    
    if disconnected:
        logger.info(f"User {current_user.email} disconnected Google Sheets")
        return {
            "success": True,
            "message": "Google Sheets disconnected successfully"
        }
    else:
        return {
            "success": True,
            "message": "No active Google Sheets integration found"
        }


@router.get("/test-connection")
async def test_google_connection(
    current_user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test Google Sheets connection by verifying the access token works.
    
    Returns:
        Connection status and user info from Google
    """
    google_service = get_google_oauth_service()
    
    access_token = google_service.get_valid_access_token(db, str(current_user.id))
    
    if not access_token:
        return {
            "connected": False,
            "error": "No active integration or token refresh failed"
        }
    
    try:
        user_info = google_service.get_user_info(access_token)
        return {
            "connected": True,
            "google_email": user_info.get('email'),
            "google_name": user_info.get('name')
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }
