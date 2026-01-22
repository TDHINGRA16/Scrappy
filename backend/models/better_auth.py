"""
BetterAuth Database Models

Maps to BetterAuth's database schema for session verification.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class BetterAuthSession(Base):
    """BetterAuth session table model"""
    __tablename__ = "session"
    
    id = Column(String, primary_key=True)
    userId = Column(String, nullable=False, index=True)
    expiresAt = Column(DateTime, nullable=False)
    token = Column(String, nullable=False, unique=True, index=True)
    ipAddress = Column(String, nullable=True)
    userAgent = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BetterAuthUser(Base):
    """BetterAuth user table model"""
    __tablename__ = "user"
    
    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True, index=True)
    emailVerified = Column(Boolean, default=False)
    name = Column(String, nullable=True)
    image = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
