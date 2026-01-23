"""
User Model for Scrappy v2.0

SQLAlchemy model for storing user authentication data.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
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
    
    Compatible with BetterAuth schema (camelCase columns):
    - id: String (matches BetterAuth generated IDs)
    - email: String
    - emailVerified: Boolean
    - createdAt, updatedAt: DateTime
    """
    __tablename__ = "user"
    
    # Primary key - Changed to String for BetterAuth compatibility
    id = Column(
        String, 
        primary_key=True, 
        index=True
    )
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=True) # For email/password auth
    
    # Profile fields
    name = Column(String(255), nullable=True)
    image = Column(Text, nullable=True)
    
    # BetterAuth uses camelCase columns by default
    emailVerified = Column(Boolean, default=False)
    
    # Timestamps (camelCase for BetterAuth)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    integrations = relationship(
        "UserIntegration", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "image": self.image,
            "emailVerified": self.emailVerified,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
        }


class Session(Base):
    """BetterAuth Session Table"""
    __tablename__ = "session"
    
    id = Column(String, primary_key=True)
    expiresAt = Column(DateTime, nullable=False)
    token = Column(String, nullable=False, unique=True, index=True)
    ipAddress = Column(String, nullable=True)
    userAgent = Column(String, nullable=True)
    
    # Foreign Key - Changed to String
    userId = Column(
        String, 
        ForeignKey('user.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")


class Account(Base):
    """BetterAuth Account Table (for OAuth)"""
    __tablename__ = "account"
    
    id = Column(String, primary_key=True)
    accountId = Column(String, nullable=False)
    providerId = Column(String, nullable=False)
    
    # Foreign Key - Changed to String
    userId = Column(
        String, 
        ForeignKey('user.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    accessToken = Column(String, nullable=True)
    refreshToken = Column(String, nullable=True)
    expiresAt = Column(DateTime, nullable=True)
    password = Column(String, nullable=True)
    
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="accounts")


class Verification(Base):
    """BetterAuth Verification Table (for email verification)"""
    __tablename__ = "verification"
    
    id = Column(String, primary_key=True)
    identifier = Column(String, nullable=False)
    value = Column(String, nullable=False)
    expiresAt = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

