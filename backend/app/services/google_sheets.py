import json
import gspread
import pandas as pd
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
from app.config import settings
from app.utils.loggers import logger

class GoogleSheetsService:
    """Enhanced Google Sheets service using service account for automatic data saving"""
    
    def __init__(self):
        self.credentials = None
        self.client = None
        self._setup_service_account()
    
    def _setup_service_account(self):
        """Setup Google Sheets service account authentication"""
        try:
            # Create credentials dict from environment variables
            credentials_dict = {
                "type": settings.GOOGLE_SERVICE_ACCOUNT_TYPE,
                "project_id": settings.GOOGLE_SERVICE_ACCOUNT_PROJECT_ID,
                "private_key_id": settings.GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID,
                "private_key": settings.GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY.replace('\\n', '\n'),
                "client_email": settings.GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL,
                "client_id": settings.GOOGLE_SERVICE_ACCOUNT_CLIENT_ID,
                "auth_uri": settings.GOOGLE_SERVICE_ACCOUNT_AUTH_URI,
                "token_uri": settings.GOOGLE_SERVICE_ACCOUNT_TOKEN_URI,
                "auth_provider_x509_cert_url": settings.GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL,
                "client_x509_cert_url": settings.GOOGLE_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL,
                "universe_domain": settings.GOOGLE_SERVICE_ACCOUNT_UNIVERSE_DOMAIN
            }
            
            # Create credentials
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            self.credentials = Credentials.from_service_account_info(
                credentials_dict, scopes=scopes
            )
            
            # Create gspread client
            self.client = gspread.authorize(self.credentials)
            logger.info("Google Sheets service account authentication successful")
            
        except Exception as e:
            logger.error(f"Failed to setup Google Sheets authentication: {str(e)}")
            self.client = None
    
    async def save_scrape_results_to_sheet(
        self, 
        results: List[Dict[str, Any]], 
        sheet_id: str = None,
        worksheet_name: str = "Scrape Results"
    ) -> bool:
        """
        Save scrape results to Google Sheets
        
        Args:
            results: List of scrape result dictionaries
            sheet_id: Google Sheet ID (uses default if not provided)
            worksheet_name: Name of the worksheet to save to
            
        Returns:
            bool: Success status
        """
        try:
            if not self.client:
                logger.error("Google Sheets client not initialized")
                return False
            
            if not results:
                logger.warning("No results to save to Google Sheets")
                return False
            
            # Use default sheet ID if not provided
            if not sheet_id:
                sheet_id = settings.DEFAULT_GOOGLE_SHEET_ID
            
            # Open the spreadsheet
            try:
                spreadsheet = self.client.open_by_key(sheet_id)
            except Exception as e:
                logger.error(f"Failed to open Google Sheet {sheet_id}: {str(e)}")
                return False
            
            # Try to get existing worksheet or create new one
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
                logger.info(f"Found existing worksheet: {worksheet_name}")
            except gspread.WorksheetNotFound:
                # Create new worksheet
                worksheet = spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=20
                )
                logger.info(f"Created new worksheet: {worksheet_name}")
            
            # Convert results to DataFrame
            df = pd.DataFrame(results)
            
            # Add timestamp column
            from datetime import datetime
            df['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Clear existing content and set new data
            worksheet.clear()
            set_with_dataframe(worksheet, df, include_index=False, include_column_header=True)
            
            logger.info(f"Successfully saved {len(results)} results to Google Sheet")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to Google Sheets: {str(e)}")
            return False
    
    async def append_scrape_results_to_sheet(
        self, 
        results: List[Dict[str, Any]], 
        sheet_id: str = None,
        worksheet_name: str = "Scrape Results"
    ) -> bool:
        """
        Append scrape results to existing Google Sheets data
        
        Args:
            results: List of scrape result dictionaries
            sheet_id: Google Sheet ID (uses default if not provided)
            worksheet_name: Name of the worksheet to append to
            
        Returns:
            bool: Success status
        """
        try:
            if not self.client:
                logger.error("Google Sheets client not initialized")
                return False
            
            if not results:
                logger.warning("No results to append to Google Sheets")
                return False
            
            # Use default sheet ID if not provided
            if not sheet_id:
                sheet_id = settings.DEFAULT_GOOGLE_SHEET_ID
            
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Try to get existing worksheet or create new one
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                # Create new worksheet if it doesn't exist
                worksheet = spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=20
                )
                # Add headers for new worksheet
                headers = list(results[0].keys()) + ['scraped_at']
                worksheet.append_row(headers)
            
            # Add timestamp to each result
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Append each result as a new row
            for result in results:
                row_data = list(result.values()) + [timestamp]
                worksheet.append_row(row_data)
            
            logger.info(f"Successfully appended {len(results)} results to Google Sheet")
            return True
            
        except Exception as e:
            logger.error(f"Error appending to Google Sheets: {str(e)}")
            return False
    
    async def create_new_sheet_for_job(
        self, 
        job_id: int, 
        query: str, 
        results: List[Dict[str, Any]]
    ) -> bool:
        """
        Create a new Google Sheet specifically for a scraping job
        
        Args:
            job_id: The job ID
            query: The search query used
            results: List of scrape result dictionaries
            
        Returns:
            bool: Success status
        """
        try:
            if not self.client:
                logger.error("Google Sheets client not initialized")
                return False
            
            # Create a new spreadsheet
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            sheet_title = f"ScrapeJob_{job_id}_{query.replace(' ', '_')}_{timestamp}"
            
            # Create the spreadsheet
            spreadsheet = self.client.create(sheet_title)
            
            # Get the default worksheet
            worksheet = spreadsheet.sheet1
            worksheet.update_title("Results")
            
            # Add job info at the top
            worksheet.update('A1:C3', [
                ['Job ID:', job_id, ''],
                ['Query:', query, ''],
                ['Scraped At:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ''],
                ['', '', '']  # Empty row
            ])
            
            # Convert results to DataFrame and add to sheet
            if results:
                df = pd.DataFrame(results)
                # Start from row 5 to leave space for job info
                set_with_dataframe(worksheet, df, row=5, include_index=False, include_column_header=True)
            
            logger.info(f"Created new Google Sheet: {sheet_title}")
            logger.info(f"Sheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating new Google Sheet: {str(e)}")
            return False
            logger.error(f"Google Sheets authentication error: {str(e)}")
            raise

    async def get_sheet_data(self, sheet_id: str, range_name: str = "A:Z") -> List[List[str]]:
        """Get data from a Google Sheet"""
        if not self.access_token:
            raise Exception("Not authenticated. Please authenticate first.")
        
        try:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_name}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("values", [])
                else:
                    raise Exception(f"Failed to fetch sheet data: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error fetching Google Sheet data: {str(e)}")
            raise

    async def parse_contacts_from_sheet(
        self, 
        sheet_data: List[List[str]]
    ) -> List[Dict[str, str]]:
        """Parse contact information from sheet data"""
        if not sheet_data:
            return []
        
        # Assume first row contains headers
        headers = [header.lower().strip() for header in sheet_data[0]]
        contacts = []
        
        # Map common header variations
        header_mapping = {
            'name': ['name', 'business_name', 'company', 'business'],
            'email': ['email', 'email_address', 'e-mail'],
            'phone': ['phone', 'phone_number', 'mobile', 'contact'],
            'website': ['website', 'url', 'web', 'site'],
            'address': ['address', 'location', 'addr']
        }
        
        # Find column indices for each field
        field_indices = {}
        for field, variations in header_mapping.items():
            for i, header in enumerate(headers):
                if any(var in header for var in variations):
                    field_indices[field] = i
                    break
        
        # Process data rows
        for row in sheet_data[1:]:  # Skip header row
            if not row:  # Skip empty rows
                continue
                
            contact = {}
            for field, index in field_indices.items():
                if index < len(row):
                    value = row[index].strip()
                    if value:  # Only add non-empty values
                        contact[field] = value
            
            # Only add contacts that have at least name and (email or phone)
            if contact.get('name') and (contact.get('email') or contact.get('phone')):
                contacts.append(contact)
        
        logger.info(f"Parsed {len(contacts)} contacts from Google Sheet")
        return contacts

    async def export_to_sheet(
        self,
        sheet_id: str,
        data: List[Dict[str, Any]],
        sheet_name: str = "Exported_Data",
        range_name: str = "A1"
    ) -> bool:
        """Export data to a Google Sheet"""
        if not self.access_token:
            raise Exception("Not authenticated. Please authenticate first.")
        
        try:
            if not data:
                raise Exception("No data to export")
            
            # Prepare headers and values
            headers = list(data[0].keys())
            values = [headers]
            
            for item in data:
                row = [str(item.get(header, '')) for header in headers]
                values.append(row)
            
            # Update sheet
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{sheet_name}!{range_name}"
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url,
                    json={
                        "values": values,
                        "majorDimension": "ROWS"
                    },
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    params={"valueInputOption": "RAW"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully exported {len(data)} rows to Google Sheet")
                    return True
                else:
                    raise Exception(f"Export failed: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error exporting to Google Sheet: {str(e)}")
            raise

    def get_auth_url(self) -> str:
        """Get Google OAuth authorization URL"""
        scopes = "https://www.googleapis.com/auth/spreadsheets"
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={self.client_id}&"
            f"redirect_uri=urn:ietf:wg:oauth:2.0:oob&"
            f"scope={scopes}&"
            f"response_type=code&"
            f"access_type=offline"
        )
        return auth_url

    def save_scraper_results_sync(self, results: List[Dict[str, Any]], job_id: int, query: str, sheet_id: str = None) -> bool:
        """
        Synchronously save scraper results to Google Sheets
        Creates a new worksheet for each scraping job
        """
        if not self.client:
            logger.error("Google Sheets client not initialized")
            return False
        
        try:
            # Use default sheet ID if not provided
            if not sheet_id:
                sheet_id = settings.DEFAULT_GOOGLE_SHEET_ID
            
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            
            # Create worksheet name with job info
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            worksheet_name = f"Job_{job_id}_{timestamp}"
            
            # Ensure worksheet name is valid (max 100 chars)
            if len(worksheet_name) > 100:
                worksheet_name = f"Job_{job_id}_{timestamp[:8]}"
            
            # Create new worksheet
            try:
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            except Exception as e:
                logger.warning(f"Could not create new worksheet, using existing: {str(e)}")
                # Try to use an existing worksheet or create with different name
                worksheet_name = f"Results_{timestamp}"
                try:
                    worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
                except:
                    # Use the first available worksheet
                    worksheet = spreadsheet.sheet1
            
            if not results:
                logger.warning("No results to save to Google Sheets")
                return False
            
            # Convert results to DataFrame
            df = pd.DataFrame(results)
            
            # Add metadata
            metadata_df = pd.DataFrame([
                ['Job ID', job_id],
                ['Query', query],
                ['Total Results', len(results)],
                ['Generated At', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ['', '']  # Empty row for separation
            ], columns=['Field', 'Value'])
            
            # Clear the worksheet first
            worksheet.clear()
            
            # Write metadata first
            set_with_dataframe(worksheet, metadata_df, row=1, col=1, include_index=False, include_column_header=True)
            
            # Write results starting after metadata
            start_row = len(metadata_df) + 3  # +3 for headers and spacing
            set_with_dataframe(worksheet, df, row=start_row, col=1, include_index=False, include_column_header=True)
            
            logger.info(f"Successfully saved {len(results)} results to Google Sheets worksheet '{worksheet_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save results to Google Sheets: {str(e)}")
            return False

    def get_sheet_info(self, sheet_id: str = None) -> dict:
        """
        Get information about the spreadsheet
        """
        if not self.client:
            return {"error": "Google Sheets client not initialized"}
        
        try:
            # Use default sheet ID if not provided
            if not sheet_id:
                sheet_id = settings.DEFAULT_GOOGLE_SHEET_ID
            
            spreadsheet = self.client.open_by_key(sheet_id)
            
            worksheets = []
            for ws in spreadsheet.worksheets():
                worksheets.append({
                    "name": ws.title,
                    "rows": ws.row_count,
                    "cols": ws.col_count,
                    "id": ws.id
                })
            
            return {
                "title": spreadsheet.title,
                "id": spreadsheet.id,
                "url": spreadsheet.url,
                "worksheets": worksheets
            }
            
        except Exception as e:
            logger.error(f"Failed to get sheet info: {str(e)}")
            return {"error": str(e)}

# Global instance
sheets_service = GoogleSheetsService()

# Convenience functions for backward compatibility
async def import_from_sheets(sheet_id: str, range_name: str = "A:Z") -> List[Dict[str, str]]:
    """Import contacts from Google Sheets"""
    try:
        sheet_data = await sheets_service.get_sheet_data(sheet_id, range_name)
        contacts = await sheets_service.parse_contacts_from_sheet(sheet_data)
        return contacts
    except Exception as e:
        logger.error(f"Google Sheets import failed: {str(e)}")
        raise

async def export_to_sheets(
    sheet_id: str, 
    data: List[Dict[str, Any]], 
    sheet_name: str = "Exported_Data"
) -> bool:
    """Export data to Google Sheets"""
    try:
        return await sheets_service.export_to_sheet(sheet_id, data, sheet_name)
    except Exception as e:
        logger.error(f"Google Sheets export failed: {str(e)}")
        raise
