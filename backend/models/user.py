"""
User Model for Scrappy v2.0

SQLAlchemy model for storing user authentication data.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base


class User(Base):
    """
    User model - stores authentication info
    
    Compatible with BetterAuth patterns:
    - UUID primary key
    - Email as unique identifier
    - bcrypt password hash
    - Timestamps for audit
    """
    __tablename__ = "user"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True
    )
    
    # Authentication fields
    email = Column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True
    )
    password_hash = Column(
        String(255), 
        nullable=False
    )
    # BetterAuth compatibility: add password column (same as password_hash)
    password = Column(
        String(255),
        nullable=True  # Nullable for backward compatibility
    )
    
    # Profile fields
    name = Column(String(255), nullable=True)
    image = Column(Text, nullable=True)  # Profile image URL
    
    # Status fields
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    integrations = relationship(
        "UserIntegration", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "image": self.image,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# NOTE: The old "Session" model for "sessions" table was removed.
# Better Auth uses the "session" table (singular) defined in models/better_auth.py
# The unused "sessions" table should be dropped from the database manually.
