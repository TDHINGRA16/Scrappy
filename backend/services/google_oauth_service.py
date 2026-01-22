"""
Google OAuth Service for Scrappy v2.0

Handles Google OAuth 2.0 flow for per-user Google Sheets integration.
Each user can connect their own Google account to save scraped data.
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import secrets

from config import settings
from services.encryption_service import get_encryption_service
from models.user_integration import UserIntegration
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """
    Handles Google OAuth 2.0 flow and Google Sheets API operations.

    Environment Variables Required:
        GOOGLE_CLIENT_ID: OAuth 2.0 client ID from Google Cloud Console
        GOOGLE_CLIENT_SECRET: OAuth 2.0 client secret
        GOOGLE_REDIRECT_URI: Callback URL (e.g., http://localhost:3000/api/integrations/google/callback)
    
    Flow:
        1. get_authorization_url() - Generate URL to redirect user to Google
        2. exchange_code_for_tokens() - Exchange authorization code for tokens
        3. save_user_integration() - Store encrypted tokens in database
        4. Use get_valid_access_token() for API calls (auto-refreshes)
    """

    SCOPES = [
        'openid',                                             # Required by Google
        'https://www.googleapis.com/auth/spreadsheets',       # Read/write sheets
        'https://www.googleapis.com/auth/userinfo.email',     # Get user email
        'https://www.googleapis.com/auth/userinfo.profile',   # Get user profile
    ]

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self._initialized = False
        
        if all([self.client_id, self.client_secret, self.redirect_uri]):
            self._initialized = True
            logger.info(f"✅ Google OAuth configured with redirect URI: {self.redirect_uri}")
        else:
            logger.warning("⚠️ Google OAuth not fully configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI")

    def _check_initialized(self):
        """Ensure service is properly configured"""
        if not self._initialized:
            raise ValueError(
                "Google OAuth not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI in .env"
            )

    def _get_client_config(self) -> dict:
        """Get OAuth client configuration"""
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate Google OAuth authorization URL.

        Args:
            state: Optional CSRF protection state (generated if not provided)

        Returns:
            Tuple of (authorization_url, state)
        """
        self._check_initialized()
        
        if not state:
            state = secrets.token_urlsafe(32)

        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )

        authorization_url, _ = flow.authorization_url(
            access_type='offline',          # Request refresh token
            include_granted_scopes='true',
            state=state,
            prompt='consent'                # Force consent to always get refresh token
        )

        return authorization_url, state

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from Google callback

        Returns:
            Dictionary with tokens: {access_token, refresh_token, expiry, ...}
        """
        self._check_initialized()
        
        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes) if credentials.scopes else [],
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }

    def refresh_access_token(self, credentials_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token.

        Args:
            credentials_dict: Credentials dictionary with refresh_token

        Returns:
            Updated credentials dictionary with new access token
        """
        credentials = Credentials(
            token=credentials_dict.get('access_token'),
            refresh_token=credentials_dict.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        credentials.refresh(Request())

        return {
            **credentials_dict,
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token or credentials_dict.get('refresh_token'),
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user's Google account information.

        Args:
            access_token: Valid access token

        Returns:
            Dictionary with user info (email, name, picture, etc.)
        """
        credentials = Credentials(token=access_token)

        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
        except HttpError as e:
            logger.error(f"Failed to get Google user info: {e}")
            raise Exception(f"Failed to get user info: {e}")

    def create_spreadsheet(self, access_token: str, title: str, sheet_name: str = "Scrappy Results") -> Dict[str, Any]:
        """
        Create a new Google Spreadsheet.

        Args:
            access_token: Valid access token
            title: Title for the new spreadsheet
            sheet_name: Name of the first sheet (default: "Scrappy Results")

        Returns:
            Dictionary with spreadsheet info (spreadsheetId, spreadsheetUrl)
        """
        credentials = Credentials(token=access_token)

        try:
            service = build('sheets', 'v4', credentials=credentials)
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [{
                    'properties': {
                        'title': sheet_name
                    }
                }]
            }
            result = service.spreadsheets().create(
                body=spreadsheet, 
                fields='spreadsheetId,spreadsheetUrl'
            ).execute()
            
            logger.info(f"Created spreadsheet: {result.get('spreadsheetId')} with sheet: {sheet_name}")
            return result
        except HttpError as e:
            logger.error(f"Failed to create spreadsheet: {e}")
            raise Exception(f"Failed to create spreadsheet: {e}")

    def write_to_sheet(
        self,
        access_token: str,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = 'USER_ENTERED'
    ) -> Dict[str, Any]:
        """
        Write data to Google Sheet (overwrites existing data in range).

        Args:
            access_token: Valid access token
            spreadsheet_id: Target spreadsheet ID
            range_name: A1 notation range (e.g., 'Sheet1!A1:G10')
            values: 2D array of values to write
            value_input_option: 'RAW' or 'USER_ENTERED' (parses formulas)

        Returns:
            Update response from Sheets API
        """
        credentials = Credentials(token=access_token)

        try:
            service = build('sheets', 'v4', credentials=credentials)
            body = {'values': values}
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            logger.info(f"Updated {result.get('updatedCells', 0)} cells in {spreadsheet_id}")
            return result
        except HttpError as e:
            logger.error(f"Failed to write to sheet: {e}")
            raise Exception(f"Failed to write to sheet: {e}")

    def append_to_sheet(
        self,
        access_token: str,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = 'USER_ENTERED'
    ) -> Dict[str, Any]:
        """
        Append data to Google Sheet (adds rows at the end).

        Args:
            access_token: Valid access token
            spreadsheet_id: Target spreadsheet ID
            range_name: A1 notation range (e.g., 'Sheet1!A:G')
            values: 2D array of values to append
            value_input_option: 'RAW' or 'USER_ENTERED'

        Returns:
            Append response from Sheets API
        """
        credentials = Credentials(token=access_token)

        try:
            service = build('sheets', 'v4', credentials=credentials)
            body = {'values': values}
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Appended {len(values)} rows to {spreadsheet_id}")
            return result
        except HttpError as e:
            logger.error(f"Failed to append to sheet: {e}")
            raise Exception(f"Failed to append to sheet: {e}")

    def save_user_integration(
        self,
        db: Session,
        user_id: str,
        credentials: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserIntegration:
        """
        Save or update user's Google Sheets integration with encrypted tokens.

        Args:
            db: Database session
            user_id: User UUID (string)
            credentials: Credentials dictionary from OAuth flow
            metadata: Optional metadata (google_email, preferences, etc.)

        Returns:
            UserIntegration instance
        """
        encryption_service = get_encryption_service()
        
        # Encrypt credentials before storage
        encrypted = encryption_service.encrypt_credentials(credentials)
        
        # Parse token expiry
        token_expires_at = None
        if credentials.get('expiry'):
            try:
                token_expires_at = datetime.fromisoformat(credentials['expiry'])
            except:
                pass

        # Check if integration already exists
        integration = db.query(UserIntegration).filter(
            UserIntegration.user_id == user_id,
            UserIntegration.integration_type == 'google_sheets'
        ).first()

        if integration:
            # Update existing integration
            integration.encrypted_credentials = encrypted
            integration.integration_metadata = {
                **(integration.integration_metadata or {}),
                **(metadata or {})
            }
            integration.is_active = True
            integration.token_expires_at = token_expires_at
            integration.updated_at = datetime.utcnow()
            logger.info(f"Updated Google Sheets integration for user {user_id}")
        else:
            # Create new integration
            integration = UserIntegration(
                user_id=user_id,
                integration_type='google_sheets',
                encrypted_credentials=encrypted,
                integration_metadata=metadata or {},
                is_active=True,
                token_expires_at=token_expires_at
            )
            db.add(integration)
            logger.info(f"Created Google Sheets integration for user {user_id}")

        db.commit()
        db.refresh(integration)
        return integration

    def get_user_integration(self, db: Session, user_id: str) -> Optional[UserIntegration]:
        """
        Get user's Google Sheets integration.

        Args:
            db: Database session
            user_id: User UUID (string)

        Returns:
            UserIntegration or None if not found
        """
        return db.query(UserIntegration).filter(
            UserIntegration.user_id == user_id,
            UserIntegration.integration_type == 'google_sheets',
            UserIntegration.is_active == True
        ).first()

    def get_valid_access_token(self, db: Session, user_id: str) -> Optional[str]:
        """
        Get valid access token for user, refreshing if necessary.

        Args:
            db: Database session
            user_id: User UUID (string)

        Returns:
            Valid access token or None if integration not found
        """
        integration = self.get_user_integration(db, user_id)
        if not integration:
            return None

        encryption_service = get_encryption_service()
        
        # Decrypt credentials
        try:
            credentials = encryption_service.decrypt_credentials(integration.encrypted_credentials)
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for user {user_id}: {e}")
            return None

        # Check if token expired or expiring soon (5 minute buffer)
        needs_refresh = False
        if credentials.get('expiry'):
            try:
                expiry = datetime.fromisoformat(credentials['expiry'])
                if expiry <= datetime.utcnow() + timedelta(minutes=5):
                    needs_refresh = True
            except:
                needs_refresh = True
        
        if needs_refresh:
            try:
                # Refresh the token
                new_credentials = self.refresh_access_token(credentials)
                
                # Save updated credentials
                encrypted = encryption_service.encrypt_credentials(new_credentials)
                integration.encrypted_credentials = encrypted
                if new_credentials.get('expiry'):
                    try:
                        integration.token_expires_at = datetime.fromisoformat(new_credentials['expiry'])
                    except:
                        pass
                integration.updated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Refreshed access token for user {user_id}")
                return new_credentials['access_token']
            except Exception as e:
                logger.error(f"Failed to refresh token for user {user_id}: {e}")
                return None

        return credentials.get('access_token')

    def disconnect_integration(self, db: Session, user_id: str) -> bool:
        """
        Disconnect user's Google Sheets integration.

        Args:
            db: Database session
            user_id: User UUID (string)

        Returns:
            True if disconnected, False if not found
        """
        integration = db.query(UserIntegration).filter(
            UserIntegration.user_id == user_id,
            UserIntegration.integration_type == 'google_sheets'
        ).first()

        if integration:
            integration.is_active = False
            integration.encrypted_credentials = None  # Clear tokens
            integration.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"Disconnected Google Sheets for user {user_id}")
            return True
        
        return False


# Singleton instance
_google_oauth_service: Optional[GoogleOAuthService] = None


def get_google_oauth_service() -> GoogleOAuthService:
    """Get singleton Google OAuth service instance"""
    global _google_oauth_service
    if _google_oauth_service is None:
        _google_oauth_service = GoogleOAuthService()
    return _google_oauth_service


google_oauth_service = get_google_oauth_service()
