"""
Authentication Service for Scrappy v2.0

BetterAuth-style authentication with:
- bcrypt password hashing
- JWT access/refresh tokens
- Database-backed user management
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
import logging
import hashlib

from models.user import User
from config import settings

logger = logging.getLogger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """JWT Token payload data"""
    email: str
    user_id: str
    exp: datetime
    iat: datetime
    token_type: str = "access"


class AuthService:
    """
    Authentication service with BetterAuth patterns
    
    Replaces hardcoded authentication with secure, database-backed auth:
    - Password hashing with bcrypt
    - JWT tokens with expiration
    - Refresh token rotation
    - Session management
    """
    
    # ============== Password Methods ==============
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    # ============== Token Methods ==============
    
    @staticmethod
    def create_access_token(user_id: str, email: str) -> Tuple[str, datetime]:
        """
        Create JWT access token
        
        Returns:
            Tuple of (token_string, expiration_datetime)
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "user_id": str(user_id),
            "email": email,
            "type": "access",
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt, expire
    
    @staticmethod
    def create_refresh_token(user_id: str, email: str) -> Tuple[str, datetime]:
        """
        Create JWT refresh token (longer expiry)
        
        Returns:
            Tuple of (token_string, expiration_datetime)
        """
        now = datetime.utcnow()
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "user_id": str(user_id),
            "email": email,
            "type": "refresh",
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt, expire
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """
        Verify and decode JWT token
        
        Returns:
            TokenData if valid, None if invalid
        """
        # Defensive checks: ensure token looks like a JWT (three segments)
        if not token or not isinstance(token, str):
            logger.warning("Empty or invalid token provided to verify_token")
            return None

        # Strip possible Bearer prefix if accidentally passed
        if token.startswith("Bearer "):
            token = token.split(" ", 1)[1]

        if token.count(".") != 2:
            snippet = token[:40] + "..." if len(token) > 40 else token
            logger.error(f"Token verification failed: invalid JWT format (not enough segments) - {snippet}")
            return None

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            email: str = payload.get("email")
            user_id: str = payload.get("user_id")
            token_type: str = payload.get("type", "access")
            
            if email is None or user_id is None:
                logger.warning("Token missing required claims")
                return None
            
            return TokenData(
                email=email,
                user_id=user_id,
                token_type=token_type,
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat")),
            )
            
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    # ============== User Management ==============
    
    @staticmethod
    def register_user(
        db: Session,
        email: str,
        password: str,
        name: Optional[str] = None
    ) -> User:
        """
        Register a new user
        
        Args:
            db: Database session
            email: User email (must be unique)
            password: Plain text password (will be hashed)
            name: Optional display name
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If email already exists
        """
        # Normalize email
        email = email.lower().strip()
        
        # Check if user exists
        existing_user = db.execute(
            select(User).where(User.email == email)
        ).scalars().first()
        
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {email}")
            raise ValueError(f"User with email {email} already exists")
        
        # Create new user with hashed password
        hashed_password = AuthService.hash_password(password)
        user = User(
            email=email,
            name=name,
            password_hash=hashed_password,
            is_active=True,
            email_verified=False,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ New user registered: {email}")
        return user
    
    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with email and password
        
        This replaces the hardcoded credential check.
        
        Args:
            db: Database session
            email: User email
            password: Plain text password
            
        Returns:
            User object if authenticated, None otherwise
        """
        # Normalize email
        email = email.lower().strip()
        
        # Find user
        user = db.execute(
            select(User).where(User.email == email)
        ).scalars().first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"Login attempt with inactive user: {email}")
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {email}")
            return None
        
        # Update last login time
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ User authenticated: {email}")
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email address"""
        return db.execute(
            select(User).where(User.email == email.lower().strip())
        ).scalars().first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.execute(
            select(User).where(User.id == user_id)
        ).scalars().first()
    
    @staticmethod
    def update_user(
        db: Session,
        user_id: str,
        name: Optional[str] = None,
        image: Optional[str] = None
    ) -> Optional[User]:
        """Update user profile"""
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        if name is not None:
            user.name = name
        if image is not None:
            user.image = image
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def change_password(
        db: Session,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password
        
        Returns:
            True if password changed, False otherwise
        """
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        if not AuthService.verify_password(current_password, user.password_hash):
            logger.warning(f"Password change failed - wrong current password for user: {user.email}")
            return False
        
        user.password_hash = AuthService.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Password changed for user: {user.email}")
        return True
    
    # ============== Session Management ==============
    
    # ============== DEPRECATED SESSION METHODS ==============
    # These methods used the old "sessions" table which has been removed.
    # Better Auth now handles sessions via the "session" table.
    # Keeping these commented for reference if needed.
    
    # @staticmethod
    # def create_session(...): ...
    # @staticmethod  
    # def invalidate_session(...): ...
    # @staticmethod
    # def invalidate_all_sessions(...): ...
