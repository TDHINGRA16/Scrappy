"""
Google Sheets Service for Scrappy v2.0

Save scraping results to Google Sheets.
Uses Google Sheets API v4 with service account authentication.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings

logger = logging.getLogger(__name__)

# Scopes required for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Default headers for the spreadsheet
DEFAULT_HEADERS = [
    'Place ID',
    'Name',
    'Address',
    'Phone',
    'Website',
    'Rating',
    'Reviews',
    'Category',
    'Hours',
    'Is Claimed',
    'Latitude',
    'Longitude',
    'Photo URL'
]


class GoogleSheetsService:
    """
    Save scraping results to Google Sheets.
    
    Requires:
    - Service account credentials JSON file
    - Spreadsheet shared with service account email
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets service.
        
        Args:
            credentials_path: Path to service account JSON file
        """
        self.credentials_path = credentials_path or settings.GOOGLE_SHEETS_CREDENTIALS_JSON
        self.service = None
        self._initialized = False
    
    def _get_credentials(self):
        """Load service account credentials"""
        if not self.credentials_path:
            raise ValueError("Google Sheets credentials path not configured")
        
        # Helper to validate and load credentials dict
        def load_creds_from_info(info):
            # Check for OAuth client credentials (web/installed) which are invalid for service account auth
            if 'web' in info or 'installed' in info:
                raise ValueError(
                    "Error: You provided OAuth Client credentials (type='web' or 'installed'), "
                    "but this backend service requires a Service Account (type='service_account').\n"
                    "Solution:\n"
                    "1. Use the 'Connect' button in the frontend Dashboard (recommended for personal accounts).\n"
                    "2. Or generate a Service Account Key in Google Cloud Console and use that JSON file."
                )
            return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

        # 1. Try to parse credentials_path as a JSON string first
        if self.credentials_path.strip().startswith('{'):
            try:
                creds_dict = json.loads(self.credentials_path)
                return load_creds_from_info(creds_dict)
            except json.JSONDecodeError:
                # If it's not valid JSON, treat it as a file path
                pass
        
        # 2. Treat as file path
        creds_path = Path(self.credentials_path)
        if not creds_path.exists():
            # If the path looks like JSON (long string starting with {), it might be a copy-paste error
            if self.credentials_path.strip().startswith('{'):
                 raise ValueError("Invalid JSON format in credential environment variable.")
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
        
        # 3. Read file and validate content
        with open(creds_path, 'r') as f:
            try:
                file_content = json.load(f)
                # We reuse the logic by passing the dict, instead of from_service_account_file directly,
                # so we can validate the type first.
                return load_creds_from_info(file_content)
            except json.JSONDecodeError:
                raise ValueError(f"File {self.credentials_path} contains invalid JSON.")
    
    def _init_service(self):
        """Initialize the Google Sheets API service"""
        if self._initialized:
            return
        
        try:
            credentials = self._get_credentials()
            self.service = build('sheets', 'v4', credentials=credentials)
            self._initialized = True
            logger.info("Google Sheets service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            raise
    
    async def create_sheet(self, title: str) -> str:
        """
        Create a new Google Spreadsheet.
        
        Args:
            title: Title for the new spreadsheet
            
        Returns:
            Spreadsheet ID of the created sheet
        """
        self._init_service()
        
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [{
                    'properties': {
                        'title': 'Scrappy Results',
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': len(DEFAULT_HEADERS)
                        }
                    }
                }]
            }
            
            result = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            spreadsheet_id = result.get('spreadsheetId')
            logger.info(f"Created new spreadsheet: {spreadsheet_id}")
            
            # Add headers
            await self._add_headers(spreadsheet_id, 'Scrappy Results')
            
            return spreadsheet_id
            
        except HttpError as e:
            logger.error(f"Error creating spreadsheet: {e}")
            raise
    
    async def _add_headers(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        headers: List[str] = None
    ) -> bool:
        """Add headers to a sheet"""
        headers = headers or DEFAULT_HEADERS
        
        try:
            range_name = f"'{sheet_name}'!A1:{chr(65 + len(headers) - 1)}1"
            
            body = {
                'values': [headers]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Added headers to {sheet_name}")
            return True
            
        except HttpError as e:
            logger.error(f"Error adding headers: {e}")
            return False
    
    async def append_results(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Append scraping results to a Google Sheet.
        
        Args:
            spreadsheet_id: ID of the Google Spreadsheet
            sheet_name: Name of the sheet to append to
            results: List of business dictionaries
            
        Returns:
            Dictionary with append status and row count
        """
        self._init_service()
        
        if not results:
            return {'success': True, 'rows_added': 0, 'message': 'No results to append'}
        
        try:
            # Check if sheet exists, create headers if needed
            await self._ensure_sheet_exists(spreadsheet_id, sheet_name)
            
            # Convert results to rows
            rows = self._results_to_rows(results)
            
            # Append to sheet
            range_name = f"'{sheet_name}'!A:M"
            
            body = {
                'values': rows
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updates = result.get('updates', {})
            rows_added = updates.get('updatedRows', len(rows))
            
            logger.info(f"Appended {rows_added} rows to {sheet_name}")
            
            return {
                'success': True,
                'rows_added': rows_added,
                'spreadsheet_id': spreadsheet_id,
                'sheet_name': sheet_name,
                'message': f'Successfully added {rows_added} rows'
            }
            
        except HttpError as e:
            logger.error(f"Error appending results: {e}")
            return {
                'success': False,
                'rows_added': 0,
                'error': str(e)
            }
    
    async def _ensure_sheet_exists(
        self,
        spreadsheet_id: str,
        sheet_name: str
    ) -> bool:
        """Ensure the sheet exists and has headers"""
        try:
            # Get spreadsheet metadata
            metadata = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            sheets = metadata.get('sheets', [])
            sheet_names = [s['properties']['title'] for s in sheets]
            
            if sheet_name not in sheet_names:
                # Create new sheet
                request = {
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': [request]}
                ).execute()
                
                logger.info(f"Created new sheet: {sheet_name}")
                
                # Add headers
                await self._add_headers(spreadsheet_id, sheet_name)
            
            return True
            
        except HttpError as e:
            logger.error(f"Error ensuring sheet exists: {e}")
            return False
    
    def _results_to_rows(self, results: List[Dict[str, Any]]) -> List[List[Any]]:
        """Convert result dictionaries to spreadsheet rows"""
        rows = []
        
        for result in results:
            row = [
                result.get('place_id', ''),
                result.get('name', ''),
                result.get('address', ''),
                result.get('phone', ''),
                result.get('website', ''),
                result.get('rating', ''),
                result.get('reviews_count', ''),
                result.get('category', ''),
                result.get('hours', ''),
                'Yes' if result.get('is_claimed') else 'No',
                result.get('latitude', ''),
                result.get('longitude', ''),
                result.get('photo_url', '')
            ]
            rows.append(row)
        
        return rows
    
    async def get_sheet_data(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        range_str: str = None
    ) -> List[List[Any]]:
        """
        Get data from a Google Sheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            sheet_name: Name of the sheet
            range_str: Optional range (e.g., "A1:M100")
            
        Returns:
            List of rows (each row is a list of values)
        """
        self._init_service()
        
        try:
            if range_str:
                range_name = f"'{sheet_name}'!{range_str}"
            else:
                range_name = f"'{sheet_name}'"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
            
        except HttpError as e:
            logger.error(f"Error getting sheet data: {e}")
            return []
    
    async def clear_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        keep_headers: bool = True
    ) -> bool:
        """
        Clear all data from a sheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            sheet_name: Name of the sheet
            keep_headers: Whether to keep the header row
            
        Returns:
            True if successful
        """
        self._init_service()
        
        try:
            start_row = 2 if keep_headers else 1
            range_name = f"'{sheet_name}'!A{start_row}:Z"
            
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                body={}
            ).execute()
            
            logger.info(f"Cleared sheet: {sheet_name}")
            return True
            
        except HttpError as e:
            logger.error(f"Error clearing sheet: {e}")
            return False


# Global instance for shared use
sheets_service = GoogleSheetsService()
