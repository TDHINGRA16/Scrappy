"""
User Integration Model for Scrappy v2.0

SQLAlchemy model for storing per-user OAuth integrations (Google Sheets, etc.)
with encrypted credentials.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base


class UserIntegration(Base):
    """
    User Integration model - stores OAuth credentials for external services
    
    Supports:
    - Google Sheets OAuth 2.0
    - Future integrations (WhatsApp, Slack, etc.)
    
    Security:
    - All credentials are encrypted before storage
    - Uses Fernet symmetric encryption
    """
    __tablename__ = "user_integrations"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign key to user table (Better Auth uses 'user' not 'users')
    user_id = Column(
        String,  # Matches User.id type (String)
        ForeignKey('user.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Integration type (google_sheets, whatsapp, slack, etc.)
    integration_type = Column(
        String(50), 
        nullable=False
    )
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Encrypted credentials (access_token, refresh_token, etc.)
    # Encrypted JSON string containing OAuth tokens
    encrypted_credentials = Column(Text, nullable=True)
    
    # Metadata (sheet IDs, connected email, preferences, etc.)
    # Stored as JSONB for flexible querying
    integration_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Token expiry tracking
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="integrations")
    
    # Constraints
    __table_args__ = (
        # One integration type per user
        UniqueConstraint('user_id', 'integration_type', name='uq_user_integration_type'),
        # Index for faster lookups
        Index('idx_user_integrations_user_type', 'user_id', 'integration_type'),
    )
    
    def __repr__(self):
        return f"<UserIntegration {self.integration_type} for user {self.user_id}>"
    
    def to_dict(self) -> dict:
        """Convert integration to dictionary (excluding sensitive data)"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "integration_type": self.integration_type,
            "is_active": self.is_active,
            "metadata": self.integration_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
