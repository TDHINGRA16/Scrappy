from pydantic import BaseModel, EmailStr
from typing import Optional, List, Literal
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    source: Literal["google_maps"] = "google_maps"
    mode: Literal["scrape_only", "scrape_and_contact"] = "scrape_only"
    message_type: Optional[Literal["whatsapp", "email", "both"]] = None
    prewritten_message: Optional[str] = None

class SearchJobResponse(BaseModel):
    job_id: int
    status: str

class ScrapeResultResponse(BaseModel):
    id: int
    name: str
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    # Review information
    reviews_count: Optional[int] = 0
    reviews_average: Optional[float] = 0.0
    
    # Business features
    store_shopping: Optional[str] = "No"
    in_store_pickup: Optional[str] = "No"
    store_delivery: Optional[str] = "No"
    
    # Additional details
    place_type: Optional[str] = None
    opening_hours: Optional[str] = None
    introduction: Optional[str] = None
    
    # Metadata
    source: str

    class Config:
        from_attributes = True

class SearchJobDetail(BaseModel):
    id: int
    query: str
    limit: Optional[int]
    mode: str
    message_type: Optional[str]
    prewritten_message: Optional[str]
    created_at: datetime
    status: str
    results: List[ScrapeResultResponse] = []

    class Config:
        from_attributes = True

class OutreachMessageResponse(BaseModel):
    id: int
    job_id: int
    contact_method: str
    recipient: str
    message: str
    status: str
    sent_at: Optional[datetime]
    error: Optional[str]

    class Config:
        from_attributes = True

class GoogleSheetImportRequest(BaseModel):
    sheet_id: str
    range: str = "A:Z"
    message_template: Optional[str] = None

class CSVImportResponse(BaseModel):
    job_id: int
    count: int
    status: str

class ExportRequest(BaseModel):
    job_id: int
    format: Literal["csv", "excel", "json"] = "csv"
    include_messages: bool = False

class BulkMessageRequest(BaseModel):
    contacts: List[dict]  # [{"email": "...", "phone": "...", "name": "..."}]
    message_template: str
    contact_method: Literal["email", "whatsapp", "both"] = "both"
    subject: Optional[str] = "Business Inquiry"

class ContactValidationRequest(BaseModel):
    emails: Optional[List[EmailStr]] = []
    phones: Optional[List[str]] = []

class ContactValidationResponse(BaseModel):
    valid_emails: List[str]
    invalid_emails: List[str]
    valid_phones: List[str]
    invalid_phones: List[str]

# Auth Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

class User(BaseModel):
    email: str
    is_active: bool = True

class UserResponse(BaseModel):
    email: str
    message: str
