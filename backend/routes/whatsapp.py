"""
WhatsApp API Routes for Scrappy v2.0

Endpoints for WhatsApp Cloud API integration:
- Connect user's WhatsApp Business account
- Send individual and bulk messages
- Template message support
- Disconnect integration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID

from middleware.auth import get_current_user
from models.better_auth import BetterAuthUser
from models.user_integration import UserIntegration
from services.whatsapp_service import whatsapp_service
from services.encryption_service import encryption_service
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


# ============================================================================
# Pydantic Models
# ============================================================================

class WhatsAppConnectRequest(BaseModel):
    """Request to connect WhatsApp Business account."""
    phone_number_id: str = Field(..., description="WhatsApp Phone Number ID")
    access_token: str = Field(..., description="WhatsApp Access Token")
    business_account_id: Optional[str] = Field(None, description="Business Account ID (optional)")
    display_name: Optional[str] = Field(None, description="Display name for this account")


class SendMessageRequest(BaseModel):
    """Request to send single WhatsApp message."""
    to: str = Field(..., description="Recipient phone number with country code")
    message: str = Field(..., max_length=4096, description="Message text")


class BulkMessageRequest(BaseModel):
    """Request to send bulk WhatsApp messages."""
    recipients: List[Dict[str, str]] = Field(
        ...,
        description="List of recipients with 'phone' and 'message' keys",
        max_length=1000
    )
    message_template: Optional[str] = Field(
        None,
        description="Message template with {name}, {phone}, {address} placeholders"
    )
    leads: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Lead data to personalize messages (alternative to recipients)"
    )
    delay_ms: int = Field(100, ge=50, le=5000, description="Delay between messages in ms")


class SendTemplateRequest(BaseModel):
    """Request to send template message."""
    to: str = Field(..., description="Recipient phone number")
    template_name: str = Field(..., description="Template name from WhatsApp Manager")
    language: str = Field('en', description="Template language code")
    parameters: Optional[List[str]] = Field(None, description="Body parameter values")
    header_params: Optional[List[str]] = Field(None, description="Header parameters")
    button_params: Optional[List[str]] = Field(None, description="Button parameters")


# ============================================================================
# Helper Functions
# ============================================================================

async def get_user_whatsapp_credentials(
    user: BetterAuthUser,
    db: Session
) -> Optional[Dict[str, str]]:
    """Get user's WhatsApp credentials from database."""
    integration = db.query(UserIntegration).filter(
        UserIntegration.user_id == user.id,
        UserIntegration.integration_type == 'whatsapp'
    ).first()

    if not integration or not integration.is_active:
        return None

    try:
        credentials = encryption_service.decrypt_credentials(
            integration.encrypted_credentials
        )
        return credentials
    except Exception:
        return None


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/connect")
async def connect_whatsapp(
    request: WhatsAppConnectRequest,
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect user's WhatsApp Business account.

    Required: Phone Number ID and Access Token from WhatsApp Business Manager.
    """
    # Verify credentials first
    verification = await whatsapp_service.verify_credentials(
        phone_number_id=request.phone_number_id,
        access_token=request.access_token
    )

    if not verification.get('valid'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid credentials: {verification.get('error', 'Verification failed')}"
        )

    # Encrypt and store credentials
    credentials = {
        'phone_number_id': request.phone_number_id,
        'access_token': request.access_token,
        'business_account_id': request.business_account_id
    }
    encrypted = encryption_service.encrypt_credentials(credentials)

    # Check for existing integration
    existing = db.query(UserIntegration).filter(
        UserIntegration.user_id == user.id,
        UserIntegration.integration_type == 'whatsapp'
    ).first()

    if existing:
        # Update existing
        existing.encrypted_credentials = encrypted
        existing.is_active = True
        existing.integration_metadata = {
            'phone_number': verification.get('phone_number'),
            'verified_name': verification.get('verified_name'),
            'quality_rating': verification.get('quality_rating'),
            'display_name': request.display_name
        }
    else:
        # Create new
        integration = UserIntegration(
            user_id=user.id,
            integration_type='whatsapp',
            encrypted_credentials=encrypted,
            integration_metadata={
                'phone_number': verification.get('phone_number'),
                'verified_name': verification.get('verified_name'),
                'quality_rating': verification.get('quality_rating'),
                'display_name': request.display_name
            }
        )
        db.add(integration)

    db.commit()

    return {
        'success': True,
        'message': 'WhatsApp account connected successfully',
        'phone_number': verification.get('phone_number'),
        'verified_name': verification.get('verified_name'),
        'quality_rating': verification.get('quality_rating')
    }


@router.get("/status")
async def get_whatsapp_status(
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get WhatsApp connection status for current user."""
    integration = db.query(UserIntegration).filter(
        UserIntegration.user_id == user.id,
        UserIntegration.integration_type == 'whatsapp'
    ).first()

    if not integration or not integration.is_active:
        return {
            'connected': False,
            'has_shared_access': whatsapp_service._initialized
        }

    metadata = integration.integration_metadata or {}
    
    return {
        'connected': True,
        'phone_number': metadata.get('phone_number'),
        'verified_name': metadata.get('verified_name'),
        'quality_rating': metadata.get('quality_rating'),
        'display_name': metadata.get('display_name'),
        'connected_at': integration.created_at.isoformat() if integration.created_at else None,
        'has_shared_access': whatsapp_service._initialized
    }


@router.post("/send")
async def send_message(
    request: SendMessageRequest,
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send WhatsApp message to single recipient."""
    # Get user credentials or use shared
    credentials = await get_user_whatsapp_credentials(user, db)

    result = await whatsapp_service.send_message(
        to=request.to,
        message=request.message,
        phone_number_id=credentials.get('phone_number_id') if credentials else None,
        access_token=credentials.get('access_token') if credentials else None
    )

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Failed to send message')
        )

    return {
        'success': True,
        'message_id': result.get('message_id'),
        'message': 'Message sent successfully'
    }


@router.post("/send-bulk")
async def send_bulk_messages(
    request: BulkMessageRequest,
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send bulk WhatsApp messages.

    Two modes:
    1. Provide 'recipients' list with pre-built messages
    2. Provide 'leads' + 'message_template' for auto-personalization
    """
    # Get user credentials
    credentials = await get_user_whatsapp_credentials(user, db)

    # Build recipients list
    if request.leads and request.message_template:
        # Auto-personalize from leads
        recipients = []
        for lead in request.leads:
            phone = lead.get('phone')
            if phone:
                message = whatsapp_service.personalize_message(
                    request.message_template,
                    lead
                )
                recipients.append({'phone': phone, 'message': message})
    elif request.recipients:
        recipients = request.recipients
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either 'recipients' or 'leads' + 'message_template'"
        )

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid recipients found"
        )

    result = await whatsapp_service.send_bulk_messages(
        recipients=recipients,
        phone_number_id=credentials.get('phone_number_id') if credentials else None,
        access_token=credentials.get('access_token') if credentials else None,
        delay_seconds=request.delay_ms / 1000
    )

    return {
        'success': True,
        'total': result['total'],
        'sent': result['success'],
        'failed': result['failed'],
        'errors': result['errors'][:10]  # First 10 errors only
    }


@router.post("/send-template")
async def send_template_message(
    request: SendTemplateRequest,
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send pre-approved template message."""
    credentials = await get_user_whatsapp_credentials(user, db)

    result = await whatsapp_service.send_template_message(
        to=request.to,
        template_name=request.template_name,
        language=request.language,
        parameters=request.parameters,
        header_params=request.header_params,
        button_params=request.button_params,
        phone_number_id=credentials.get('phone_number_id') if credentials else None,
        access_token=credentials.get('access_token') if credentials else None
    )

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Failed to send template')
        )

    return {
        'success': True,
        'message': 'Template message sent successfully'
    }


@router.get("/templates")
async def get_templates(
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of approved WhatsApp templates."""
    credentials = await get_user_whatsapp_credentials(user, db)

    if not credentials:
        # Try shared account
        result = await whatsapp_service.get_message_templates()
    else:
        result = await whatsapp_service.get_message_templates(
            business_account_id=credentials.get('business_account_id'),
            access_token=credentials.get('access_token')
        )

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Failed to fetch templates')
        )

    return {
        'success': True,
        'templates': result.get('templates', [])
    }


@router.post("/disconnect")
async def disconnect_whatsapp(
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect WhatsApp integration."""
    integration = db.query(UserIntegration).filter(
        UserIntegration.user_id == user.id,
        UserIntegration.integration_type == 'whatsapp'
    ).first()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No WhatsApp integration found"
        )

    # Soft delete - keep record but deactivate
    integration.is_active = False
    integration.encrypted_credentials = None
    db.commit()

    return {
        'success': True,
        'message': 'WhatsApp account disconnected'
    }


@router.post("/test")
async def test_connection(
    user: BetterAuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test WhatsApp connection by verifying credentials."""
    credentials = await get_user_whatsapp_credentials(user, db)

    if not credentials:
        if whatsapp_service._initialized:
            # Test shared account
            result = await whatsapp_service.verify_credentials(
                whatsapp_service.shared_phone_number_id,
                whatsapp_service.shared_access_token
            )
            return {
                'success': result.get('valid', False),
                'using': 'shared_account',
                'phone_number': result.get('phone_number'),
                'verified_name': result.get('verified_name')
            }
        else:
            return {
                'success': False,
                'error': 'No WhatsApp account connected'
            }

    result = await whatsapp_service.verify_credentials(
        credentials['phone_number_id'],
        credentials['access_token']
    )

    return {
        'success': result.get('valid', False),
        'using': 'user_account',
        'phone_number': result.get('phone_number'),
        'verified_name': result.get('verified_name'),
        'quality_rating': result.get('quality_rating'),
        'error': result.get('error') if not result.get('valid') else None
    }
