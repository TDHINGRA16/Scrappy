"""
Pydantic Models for Scrappy v2.0

Data validation and serialization models for API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any
from datetime import datetime


# ============== Business Result Models ==============

class BusinessResult(BaseModel):
    """Single business result from scraping"""
    
    place_id: Optional[str] = Field(None, description="Google Place ID (primary identifier)")
    cid: Optional[str] = Field(None, description="Customer ID (secondary identifier)")
    name: str = Field(..., description="Business name")
    address: Optional[str] = Field(None, description="Business address")
    phone: Optional[str] = Field(None, description="Business phone number")
    website: Optional[str] = Field(None, description="Business website URL")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating (0-5 stars)")
    reviews_count: Optional[int] = Field(None, ge=0, description="Number of reviews")
    category: Optional[str] = Field(None, description="Business category")
    hours: Optional[str] = Field(None, description="Opening hours")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    is_claimed: Optional[bool] = Field(False, description="Whether business is claimed")
    photo_url: Optional[str] = Field(None, description="Main photo URL")
    href: Optional[str] = Field(None, description="Full Google Maps URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "place_id": "0x890cb024fe77e7b6",
                "cid": "12345678901234567890",
                "name": "Pizza Hut",
                "address": "123 Main St, Amritsar, Punjab",
                "phone": "+91-9876543210",
                "website": "https://pizzahut.com",
                "rating": 4.5,
                "reviews_count": 342,
                "category": "Restaurant",
                "hours": "10:00 AM - 10:00 PM",
                "is_claimed": True
            }
        }


# ============== Scraping Request/Response Models ==============

class ScrapeRequest(BaseModel):
    """Request model for scraping endpoint"""
    
    search_query: str = Field(..., min_length=2, description="Search query (e.g., 'dentists in Amritsar')", alias="search_query")
    target_count: int = Field(50, ge=1, le=500, description="Number of results to collect")
    max_scrolls: int = Field(50, ge=1, le=100, description="Maximum scroll attempts")
    headless: bool = Field(True, description="Run browser in headless mode")
    
    @field_validator('search_query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Clean and validate search query"""
        return v.strip()
    
    class Config:
        populate_by_name = True  # Allow both 'search_query' and 'query'
        json_schema_extra = {
            "example": {
                "search_query": "restaurants in Amritsar",
                "target_count": 50,
                "max_scrolls": 50,
                "headless": True
            }
        }


class ScrapeStats(BaseModel):
    """Statistics from a scraping operation"""
    
    cards_found: int = Field(0, description="Total cards found before dedup")
    cards_extracted: int = Field(0, description="Cards successfully extracted")
    extraction_errors: int = Field(0, description="Extraction errors encountered")
    scrolls_performed: int = Field(0, description="Number of scrolls performed")
    stale_scrolls: int = Field(0, description="Number of stale scrolls (no new cards)")
    dedup_stats: Optional[dict] = Field(None, description="Deduplication statistics")


class ScrapeResponse(BaseModel):
    """Response model for scraping endpoint"""
    
    status: str = Field(..., description="Status of the operation")
    query: str = Field(..., description="Original search query")
    total_collected: int = Field(..., description="Total cards found before dedup")
    unique_results: int = Field(..., description="Unique results after dedup")
    target_count: int = Field(..., description="Requested target count")
    time_taken: float = Field(..., description="Time taken in seconds")
    results: List[BusinessResult] = Field(..., description="List of business results")
    stats: Optional[ScrapeStats] = Field(None, description="Scraping statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "query": "dentists in Amritsar",
                "total_collected": 87,
                "unique_results": 45,
                "target_count": 50,
                "time_taken": 42.5,
                "results": []
            }
        }


# ============== Google Sheets Models ==============

class GoogleSheetsRequest(BaseModel):
    """Request to save results to Google Sheets"""
    
    results: List[BusinessResult] = Field(..., description="Results to save")
    spreadsheet_id: Optional[str] = Field(None, description="Google Spreadsheet ID")
    sheet_name: str = Field("Scrappy Results", description="Sheet name to save to")
    query: Optional[str] = Field(None, description="Search query for naming the spreadsheet")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                "sheet_name": "Scrappy Results"
            }
        }


class GoogleSheetsResponse(BaseModel):
    """Response from Google Sheets save operation"""
    
    success: bool = Field(..., description="Whether operation was successful")
    rows_added: int = Field(0, description="Number of rows added")
    spreadsheet_id: Optional[str] = Field(None, description="Spreadsheet ID")
    sheet_name: Optional[str] = Field(None, description="Sheet name")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============== SMS Outreach Models ==============

class SMSOutreachRequest(BaseModel):
    """Request to send SMS outreach"""
    
    results: List[BusinessResult] = Field(..., description="Businesses to contact")
    message_template: str = Field(
        ...,
        min_length=10,
        max_length=160,
        description="Message template with {name}, {phone}, {address} variables"
    )
    provider: str = Field("twilio", description="SMS provider: 'twilio' or 'fast2sms'")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate SMS provider"""
        allowed = ['twilio', 'fast2sms']
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of: {allowed}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "message_template": "Hey {name}! Check out our marketing services at example.com",
                "provider": "twilio"
            }
        }


class SMSSingleResult(BaseModel):
    """Result of a single SMS send"""
    
    business: Optional[str] = Field(None, description="Business name")
    phone: str = Field(..., description="Phone number")
    success: bool = Field(..., description="Whether send was successful")
    message_sid: Optional[str] = Field(None, description="Message ID from provider")
    request_id: Optional[str] = Field(None, description="Request ID from Fast2SMS")
    error: Optional[str] = Field(None, description="Error message if failed")
    provider: Optional[str] = Field(None, description="Provider used")


class SMSOutreachResponse(BaseModel):
    """Response from SMS outreach operation"""
    
    total: int = Field(..., description="Total messages attempted")
    success: int = Field(0, description="Successful sends")
    failed: int = Field(0, description="Failed sends")
    skipped: int = Field(0, description="Skipped (no phone number)")
    provider: str = Field(..., description="Provider used")
    results: List[SMSSingleResult] = Field(..., description="Individual results")


# ============== Health Check Models ==============

class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field("alive", description="Service status")
    version: str = Field("2.0.0", description="API version")
    service: str = Field("Scrappy", description="Service name")
    timestamp: Optional[str] = Field(None, description="Current timestamp")


class ProviderStatus(BaseModel):
    """Status of a single provider"""
    
    configured: bool = Field(..., description="Whether provider is configured")
    from_number: Optional[str] = Field(None, description="From number (Twilio)")
    sender_id: Optional[str] = Field(None, description="Sender ID (Fast2SMS)")


class SMSProviderStatusResponse(BaseModel):
    """Response showing SMS provider configuration status"""
    
    current_provider: str = Field(..., description="Currently configured provider")
    twilio: ProviderStatus = Field(..., description="Twilio configuration status")
    fast2sms: ProviderStatus = Field(..., description="Fast2SMS configuration status")


# ============== Error Models ==============

class ErrorResponse(BaseModel):
    """Standard error response"""
    
    status: str = Field("error", description="Error status")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error info")
    timestamp: Optional[str] = Field(None, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Scraping failed",
                "detail": "Failed to load Google Maps",
                "timestamp": "2024-01-20T12:00:00Z"
            }
        }


# ============== Authentication Models (BetterAuth) ==============

class SignInRequest(BaseModel):
    """Sign in request"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class SignUpRequest(BaseModel):
    """Sign up request"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")
    name: Optional[str] = Field(None, description="User display name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "name": "John Doe"
            }
        }


class UserResponse(BaseModel):
    """User data response"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User display name")
    image: Optional[str] = Field(None, description="Profile image URL")
    is_active: bool = Field(True, description="Whether user is active")
    email_verified: bool = Field(False, description="Whether email is verified")
    created_at: Optional[datetime] = Field(None, description="Account creation date")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "name": "John Doe",
                "image": None,
                "is_active": True,
                "email_verified": False,
                "created_at": "2024-01-20T12:00:00Z"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response with tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration timestamp")
    user: UserResponse = Field(..., description="Authenticated user data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1705756800,
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "name": "John Doe"
                }
            }
        }


class UserUpdateRequest(BaseModel):
    """User profile update request"""
    name: Optional[str] = Field(None, description="New display name")
    image: Optional[str] = Field(None, description="New profile image URL")


class ChangePasswordRequest(BaseModel):
    """Password change request"""
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    logout_all_devices: bool = Field(False, description="Logout from all other devices")


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str = Field(..., description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }

