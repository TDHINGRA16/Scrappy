from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import SearchJob
from app.utils.loggers import logger
import re
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth import auth_service

# Email validation regex
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# Phone validation regex (supports various formats)
PHONE_REGEX = r"^(\+?1[-.\s]?)?(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}|\+?[1-9]\d{1,14})$"

security = HTTPBearer()

async def get_search_job(
    job_id: int, 
    db: AsyncSession = Depends(get_db)
) -> SearchJob:
    """Dependency to get a search job by ID"""
    result = await db.execute(select(SearchJob).where(SearchJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search job with ID {job_id} not found"
        )
    
    return job

async def get_active_search_job(
    job_id: int, 
    db: AsyncSession = Depends(get_db)
) -> SearchJob:
    """Dependency to get an active (non-failed) search job"""
    job = await get_search_job(job_id, db)
    
    if job.status.startswith("failed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} has failed and cannot be processed"
        )
    
    return job

def validate_email(email: str) -> bool:
    """Validate email format"""
    return bool(re.match(EMAIL_REGEX, email))

def validate_phone(phone: str) -> bool:
    """Validate phone format"""
    # Remove common phone formatting characters
    clean_phone = re.sub(r'[-.\s()]', '', phone)
    return bool(re.match(PHONE_REGEX, clean_phone))

def sanitize_phone(phone: str) -> str:
    """Sanitize phone number to standard format"""
    # Remove all non-digit characters except +
    clean = re.sub(r'[^\d+]', '', phone)
    
    # Add country code if missing
    if not clean.startswith('+'):
        if len(clean) == 10:
            clean = '+1' + clean  # US default
        elif len(clean) == 11 and clean.startswith('1'):
            clean = '+' + clean
    
    return clean

def validate_message_template(template: str) -> bool:
    """Validate message template has required placeholders"""
    required_placeholders = ['{name}', '{business_name}']
    return any(placeholder in template for placeholder in required_placeholders)

class PaginationParams:
    """Pagination parameters for list endpoints"""
    def __init__(self, page: int = 1, size: int = 20):
        self.page = max(1, page)
        self.size = min(100, max(1, size))  # Limit to 100 items per page
        self.offset = (self.page - 1) * self.size

def get_pagination_params(page: int = 1, size: int = 20) -> PaginationParams:
    """Dependency for pagination parameters"""
    return PaginationParams(page, size)

async def verify_job_ownership(
    job_id: int,
    user_id: str = None,  # For future auth implementation
    db: AsyncSession = Depends(get_db)
) -> SearchJob:
    """Verify job ownership (placeholder for future auth)"""
    # For now, just return the job
    # In future, add user authentication and ownership checks
    return await get_search_job(job_id, db)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to get current authenticated user"""
    try:
        user_data = auth_service.verify_token(credentials.credentials)
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_auth(user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires authentication"""
    return user
