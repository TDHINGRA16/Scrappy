"""
WhatsApp Cloud API Service for Scrappy v2.0

Provides WhatsApp messaging capabilities for bulk outreach to scraped leads.

Features:
- Send individual and bulk WhatsApp messages
- Support for user's own WhatsApp Business account
- Shared fallback account for users without own account
- Template message support (pre-approved templates)
- Rate limiting and error handling
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    WhatsApp Cloud API integration for bulk messaging.

    Supports:
    - User's own WhatsApp Business account (recommended for agencies)
    - Shared fallback account (for freelancers/new users without API access)
    
    Setup:
    1. Create WhatsApp Business account at business.facebook.com
    2. Get Phone Number ID and Access Token from WhatsApp Manager
    3. Set environment variables or store in user_integrations table
    """

    API_VERSION = 'v18.0'
    BASE_URL = 'https://graph.facebook.com'

    def __init__(self):
        # Shared/fallback account credentials (from env)
        self.shared_phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.shared_access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.shared_business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
        
        # Rate limiting
        self.messages_per_second = 10  # WhatsApp rate limit
        self.last_message_time = datetime.min
        
        self._initialized = bool(self.shared_phone_number_id and self.shared_access_token)
        
        if not self._initialized:
            logger.warning("⚠️ WhatsApp shared account not configured. Set WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN")
        else:
            logger.info("✅ WhatsApp service initialized with shared account")

    def _get_api_url(self, phone_number_id: str) -> str:
        """Get API URL for sending messages."""
        return f"{self.BASE_URL}/{self.API_VERSION}/{phone_number_id}/messages"

    async def send_message(
        self,
        to: str,
        message: str,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp text message to single recipient.

        Args:
            to: Recipient phone number (with country code, no + or spaces)
                Example: "919876543210" for India
            message: Message text (max 4096 characters)
            phone_number_id: User's phone number ID (uses shared if not provided)
            access_token: User's access token (uses shared if not provided)

        Returns:
            Dict with 'success' boolean and 'data' or 'error'
        """
        # Use user's credentials or fallback to shared
        phone_id = phone_number_id or self.shared_phone_number_id
        token = access_token or self.shared_access_token

        if not phone_id or not token:
            return {
                'success': False,
                'error': 'WhatsApp credentials not configured. Connect your account or use shared.'
            }

        # Clean phone number (remove +, spaces, dashes)
        clean_phone = ''.join(filter(str.isdigit, to))
        
        if len(clean_phone) < 10:
            return {
                'success': False,
                'error': f'Invalid phone number: {to}'
            }

        url = self._get_api_url(phone_id)

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': clean_phone,
            'type': 'text',
            'text': {
                'preview_url': True,  # Enable link previews
                'body': message[:4096]  # WhatsApp limit
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )

                result = response.json()

                if response.status_code == 200:
                    logger.info(f"✅ WhatsApp sent to {clean_phone[-4:]}")
                    return {
                        'success': True,
                        'data': result,
                        'message_id': result.get('messages', [{}])[0].get('id')
                    }
                else:
                    error_msg = result.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"❌ WhatsApp failed to {clean_phone[-4:]}: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'error_code': result.get('error', {}).get('code')
                    }

        except httpx.TimeoutException:
            logger.error(f"Timeout sending to {clean_phone[-4:]}")
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Error sending to {clean_phone[-4:]}: {e}")
            return {'success': False, 'error': str(e)}

    async def send_bulk_messages(
        self,
        recipients: List[Dict[str, str]],
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
        delay_seconds: float = 0.1
    ) -> Dict[str, Any]:
        """
        Send bulk WhatsApp messages with personalization.

        Args:
            recipients: List of dicts with 'phone' and 'message' keys
                Example: [{"phone": "919876543210", "message": "Hi John!"}]
            phone_number_id: User's phone number ID (optional)
            access_token: User's access token (optional)
            delay_seconds: Delay between messages (rate limiting)

        Returns:
            Summary dict with total, success, failed counts and errors
        """
        if len(recipients) > 1000:
            return {
                'success': False,
                'error': 'Maximum 1000 recipients per bulk send',
                'total': len(recipients),
                'sent': 0,
                'failed': 0
            }

        results = {
            'total': len(recipients),
            'success': 0,
            'failed': 0,
            'errors': [],
            'message_ids': []
        }

        for i, recipient in enumerate(recipients):
            phone = recipient.get('phone')
            message = recipient.get('message')

            if not phone or not message:
                results['failed'] += 1
                results['errors'].append({
                    'phone': phone or 'N/A',
                    'error': 'Missing phone or message'
                })
                continue

            result = await self.send_message(
                to=phone,
                message=message,
                phone_number_id=phone_number_id,
                access_token=access_token
            )

            if result['success']:
                results['success'] += 1
                if result.get('message_id'):
                    results['message_ids'].append(result['message_id'])
            else:
                results['failed'] += 1
                results['errors'].append({
                    'phone': phone[-4:] if phone else 'N/A',  # Last 4 digits for privacy
                    'error': result.get('error', 'Unknown error')
                })

            # Rate limiting delay
            if delay_seconds > 0 and i < len(recipients) - 1:
                await asyncio.sleep(delay_seconds)

            # Progress logging
            if (i + 1) % 50 == 0:
                logger.info(f"📤 Bulk progress: {i + 1}/{len(recipients)}")

        logger.info(
            f"📊 Bulk send complete: {results['success']}/{results['total']} successful, "
            f"{results['failed']} failed"
        )
        
        return results

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language: str = 'en',
        parameters: Optional[List[str]] = None,
        header_params: Optional[List[str]] = None,
        button_params: Optional[List[str]] = None,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp template message (pre-approved templates).
        
        Templates must be approved in WhatsApp Business Manager before use.
        Required for initiating conversations with users who haven't messaged you.

        Args:
            to: Recipient phone number
            template_name: Template name from WhatsApp Manager
            language: Template language code (e.g., 'en', 'en_US', 'hi')
            parameters: Body parameter values (replaces {{1}}, {{2}}, etc.)
            header_params: Header parameter values
            button_params: Button parameter values
            phone_number_id: User's phone number ID (optional)
            access_token: User's access token (optional)

        Returns:
            Dict with 'success' boolean and 'data' or 'error'
        """
        phone_id = phone_number_id or self.shared_phone_number_id
        token = access_token or self.shared_access_token

        if not phone_id or not token:
            return {
                'success': False,
                'error': 'WhatsApp credentials not configured'
            }

        clean_phone = ''.join(filter(str.isdigit, to))
        url = self._get_api_url(phone_id)

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Build template components
        components = []
        
        if header_params:
            components.append({
                'type': 'header',
                'parameters': [{'type': 'text', 'text': param} for param in header_params]
            })
        
        if parameters:
            components.append({
                'type': 'body',
                'parameters': [{'type': 'text', 'text': param} for param in parameters]
            })
            
        if button_params:
            for i, param in enumerate(button_params):
                components.append({
                    'type': 'button',
                    'sub_type': 'quick_reply',
                    'index': str(i),
                    'parameters': [{'type': 'payload', 'payload': param}]
                })

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': clean_phone,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {
                    'code': language
                }
            }
        }
        
        if components:
            payload['template']['components'] = components

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )

                result = response.json()

                if response.status_code == 200:
                    logger.info(f"✅ Template '{template_name}' sent to {clean_phone[-4:]}")
                    return {'success': True, 'data': result}
                else:
                    error_msg = result.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"❌ Template failed: {error_msg}")
                    return {'success': False, 'error': error_msg}

        except Exception as e:
            logger.error(f"Error sending template: {e}")
            return {'success': False, 'error': str(e)}

    async def verify_credentials(
        self,
        phone_number_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Verify WhatsApp Business API credentials.

        Args:
            phone_number_id: Phone Number ID to verify
            access_token: Access Token to verify

        Returns:
            Dict with 'valid' boolean and phone info or error
        """
        url = f"{self.BASE_URL}/{self.API_VERSION}/{phone_number_id}"

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=15.0)
                result = response.json()

                if response.status_code == 200:
                    return {
                        'valid': True,
                        'phone_number': result.get('display_phone_number'),
                        'verified_name': result.get('verified_name'),
                        'quality_rating': result.get('quality_rating')
                    }
                else:
                    return {
                        'valid': False,
                        'error': result.get('error', {}).get('message', 'Invalid credentials')
                    }

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    async def get_message_templates(
        self,
        business_account_id: Optional[str] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get list of approved message templates.

        Args:
            business_account_id: WhatsApp Business Account ID
            access_token: Access token

        Returns:
            Dict with templates list or error
        """
        biz_id = business_account_id or self.shared_business_account_id
        token = access_token or self.shared_access_token

        if not biz_id or not token:
            return {
                'success': False,
                'error': 'Business Account ID not configured'
            }

        url = f"{self.BASE_URL}/{self.API_VERSION}/{biz_id}/message_templates"

        headers = {
            'Authorization': f'Bearer {token}'
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=15.0)
                result = response.json()

                if response.status_code == 200:
                    templates = result.get('data', [])
                    return {
                        'success': True,
                        'templates': [
                            {
                                'name': t.get('name'),
                                'status': t.get('status'),
                                'category': t.get('category'),
                                'language': t.get('language')
                            }
                            for t in templates
                        ]
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', {}).get('message', 'Failed to fetch templates')
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def personalize_message(
        self,
        template: str,
        lead: Dict[str, Any]
    ) -> str:
        """
        Personalize message template with lead data.

        Args:
            template: Message template with placeholders
            lead: Lead data dict

        Supported placeholders:
            {name} - Business name
            {phone} - Phone number
            {address} - Address
            {website} - Website
            {rating} - Rating
            {category} - Category
            {reviews} - Review count

        Returns:
            Personalized message string
        """
        message = template
        
        replacements = {
            '{name}': lead.get('name', 'there'),
            '{phone}': lead.get('phone', ''),
            '{address}': lead.get('address', ''),
            '{website}': lead.get('website', ''),
            '{rating}': str(lead.get('rating', '')),
            '{category}': lead.get('category', ''),
            '{reviews}': str(lead.get('reviews_count', '')),
        }
        
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value or '')
        
        return message.strip()


# Singleton instance
whatsapp_service = WhatsAppService()
