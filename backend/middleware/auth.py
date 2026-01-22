"""
Authentication Middleware for Scrappy v2.0

Provides route protection via BetterAuth session verification.
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
import logging

from database import get_db
from models.better_auth import BetterAuthSession, BetterAuthUser

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(
    scheme_name="BetterAuth Session",
    description="Enter your BetterAuth session token",
    auto_error=True
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> BetterAuthUser:
    """
    Get current authenticated user from BetterAuth session token.
    
    Verifies session by querying the database instead of JWT verification.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: BetterAuthUser = Depends(get_current_user)):
            return {"message": f"Hello {user.email}"}
    
    Raises:
        HTTPException 401: If session is invalid, expired, or user not found
    """
    token = credentials.credentials
    
    if not token or not isinstance(token, str):
        logger.warning("Empty or invalid token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Query session from database
        session = db.execute(
            select(BetterAuthSession).where(BetterAuthSession.token == token)
        ).scalars().first()
        
        if not session:
            logger.warning(f"Session not found: {token[:20]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if session expired
        now = datetime.now(timezone.utc)
        # Make expiresAt timezone-aware if it's naive
        expires_at = session.expiresAt
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now:
            logger.warning(f"Session expired: {token[:20]}... (expired at {expires_at})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user
        user = db.execute(
            select(BetterAuthUser).where(BetterAuthUser.id == session.userId)
        ).scalars().first()
        
        if not user:
            logger.error(f"User not found for session: {session.userId}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.info(f"✅ User authenticated: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> BetterAuthUser | None:
    """
    Get current user if authenticated, None otherwise.
    
    Useful for routes that have different behavior for authenticated
    vs unauthenticated users.
    
    Usage:
        @router.get("/public")
        async def public_route(user: BetterAuthUser | None = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello guest"}
    """
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ", 1)[1]
    
    try:
        # Query session from database
        session = db.execute(
            select(BetterAuthSession).where(BetterAuthSession.token == token)
        ).scalars().first()
        
        if not session:
            return None
        
        # Check if session expired
        now = datetime.now(timezone.utc)
        expires_at = session.expiresAt
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now:
            return None
        
        # Get user
        user = db.execute(
            select(BetterAuthUser).where(BetterAuthUser.id == session.userId)
        ).scalars().first()
        
        return user
        
    except Exception as e:
        logger.error(f"Optional auth error: {e}")
        return None


def require_verified_email(user: BetterAuthUser = Depends(get_current_user)) -> BetterAuthUser:
    """
    Require user to have verified email.
    
    Usage:
        @router.post("/sensitive")
        async def sensitive_route(user: BetterAuthUser = Depends(require_verified_email)):
            ...
    """
    if not user.emailVerified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return user
