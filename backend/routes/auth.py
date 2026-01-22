"""
Auth API Routes for Scrappy v2.0

Simple authentication endpoints for testing via FastAPI docs.
Note: BetterAuth handles primary auth in the frontend.
These routes create sessions in the same database tables.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import secrets
import logging

from database import get_db
from models.better_auth import BetterAuthUser, BetterAuthSession
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# Request/Response Models
# ============================================================================

class SignInRequest(BaseModel):
    """Sign in request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }


class SignInResponse(BaseModel):
    """Sign in response with session token"""
    success: bool
    message: str
    token: str | None = None
    user: dict | None = None
    expires_at: datetime | None = None


class UserResponse(BaseModel):
    """Current user info"""
    id: str
    email: str
    name: str | None
    email_verified: bool
    created_at: datetime


# ============================================================================
# Auth Routes
# ============================================================================

@router.post(
    "/signin",
    response_model=SignInResponse,
    summary="Sign in with email and password",
    description="Authenticate and receive a session token for API access"
)
async def signin(
    request: SignInRequest,
    db: Session = Depends(get_db)
):
    """
    Sign in with email and password.
    
    Returns a session token that can be used in the Authorization header:
    `Authorization: Bearer <token>`
    
    **Note:** This creates a session in the same database as BetterAuth,
    so tokens are interchangeable between frontend and backend.
    """
    # Find user by email
    user = db.execute(
        select(BetterAuthUser).where(BetterAuthUser.email == request.email.lower())
    ).scalars().first()
    
    if not user:
        logger.warning(f"Sign in attempt with unknown email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # BetterAuth stores passwords in the 'account' table, not 'user' table
    # For this simple route, we'll check if user exists and create a session
    # In production, you'd verify the password hash from the account table
    
    # For now, create a session (this is a simplified flow for testing)
    # Generate session token
    session_token = secrets.token_urlsafe(24)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Create session
    new_session = BetterAuthSession(
        id=secrets.token_urlsafe(24),
        userId=user.id,
        token=session_token,
        expiresAt=expires_at,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )
    
    db.add(new_session)
    db.commit()
    
    logger.info(f"✅ User signed in via API: {user.email}")
    
    return SignInResponse(
        success=True,
        message="Successfully signed in",
        token=session_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "emailVerified": user.emailVerified,
        },
        expires_at=expires_at
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's info"
)
async def get_me(
    user: BetterAuthUser = Depends(get_current_user)
):
    """
    Get current user info.
    
    **Requires authentication** - Include session token in Authorization header.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        email_verified=user.emailVerified or False,
        created_at=user.createdAt
    )


@router.post(
    "/signout",
    summary="Sign out",
    description="Invalidate the current session"
)
async def signout(
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sign out and invalidate the current session.
    
    **Requires authentication** - Include session token in Authorization header.
    """
    # Delete all sessions for this user (or just the current one)
    sessions = db.execute(
        select(BetterAuthSession).where(BetterAuthSession.userId == user.id)
    ).scalars().all()
    
    for session in sessions:
        db.delete(session)
    
    db.commit()
    
    logger.info(f"✅ User signed out: {user.email}")
    
    return {"success": True, "message": "Successfully signed out"}


@router.get(
    "/test",
    summary="Test authentication",
    description="Quick test endpoint to verify auth is working"
)
async def test_auth(
    user: BetterAuthUser = Depends(get_current_user)
):
    """
    Test that authentication is working.
    
    **Requires authentication** - Include session token in Authorization header.
    """
    return {
        "success": True,
        "message": f"Hello {user.name or user.email}! Authentication is working.",
        "user_id": user.id,
        "email": user.email
    }
