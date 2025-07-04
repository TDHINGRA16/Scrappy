from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class SearchJob(Base):
    __tablename__ = "search_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    limit = Column(Integer, default=None)
    source = Column(String, default="google")  # 'google' or 'google_maps'
    mode = Column(String)  # 'scrape_only' or 'scrape_and_contact'
    message_type = Column(String, nullable=True)  # 'whatsapp', 'email', 'both'
    prewritten_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    
    results = relationship("ScrapeResult", back_populates="job")
    messages = relationship("OutreachMessage", back_populates="job")

class ScrapeResult(Base):
    __tablename__ = "scrape_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("search_jobs.id"))
    
    # Basic information
    name = Column(String, nullable=False)
    website = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    # Review information
    reviews_count = Column(Integer, nullable=True, default=0)
    reviews_average = Column(Float, nullable=True, default=0.0)
    
    # Business features
    store_shopping = Column(String, nullable=True, default="No")  # Yes/No
    in_store_pickup = Column(String, nullable=True, default="No")  # Yes/No
    store_delivery = Column(String, nullable=True, default="No")  # Yes/No
    
    # Additional details
    place_type = Column(String, nullable=True)
    opening_hours = Column(String, nullable=True)
    introduction = Column(Text, nullable=True)
    
    # Metadata
    source = Column(String, default="google_maps")  # Google, Google Maps, Yelp, etc.
    place_id = Column(String, nullable=True)  # Google Maps place IDs
    
    job = relationship("SearchJob", back_populates="results")

class OutreachMessage(Base):
    __tablename__ = "outreach_messages"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("search_jobs.id"))
    contact_method = Column(String)  # whatsapp/email
    recipient = Column(String)  # phone/email
    message = Column(String)
    status = Column(String, default="pending")  # pending, sent, failed
    sent_at = Column(DateTime, nullable=True)
    error = Column(String, nullable=True)
    
    job = relationship("SearchJob", back_populates="messages")