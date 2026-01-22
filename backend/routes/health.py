"""
Health check endpoints for Scrappy v2.0
"""

from fastapi import APIRouter
from datetime import datetime

from models.schemas import HealthResponse, SMSProviderStatusResponse
from services.sms_service import sms_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.
    
    Returns service status and version information.
    """
    return HealthResponse(
        status="alive",
        version="2.0.0",
        service="Scrappy",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint.
    
    Returns a pong response to verify service is reachable.
    """
    return {"pong": True, "timestamp": datetime.utcnow().isoformat()}


@router.get("/status")
async def status():
    """
    Detailed status endpoint.
    
    Returns service status with configuration details.
    """
    return {
        "status": "running",
        "version": "2.0.0",
        "service": "Scrappy",
        "description": "Google Maps Lead Scraper API",
        "endpoints": {
            "docs": "/docs",
            "scrape": "/api/scrape",
            "save_to_sheets": "/api/save-to-sheets",
            "send_outreach": "/api/send-outreach",
            "health": "/health"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/sms-status", response_model=SMSProviderStatusResponse)
async def sms_provider_status():
    """
    Check SMS provider configuration status.
    
    Returns which SMS providers are configured and ready to use.
    """
    status = sms_service.get_provider_status()
    
    return SMSProviderStatusResponse(
        current_provider=status['current_provider'],
        twilio={
            'configured': status['twilio']['configured'],
            'from_number': status['twilio']['from_number']
        },
        fast2sms={
            'configured': status['fast2sms']['configured'],
            'sender_id': status['fast2sms']['sender_id']
        }
    )
