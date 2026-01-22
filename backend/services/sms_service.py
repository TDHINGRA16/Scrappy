"""
SMS Outreach Service for Scrappy v2.0

Send SMS messages to scraped businesses.
Supports multiple providers:
- Twilio (international)
- Fast2SMS (India-focused)
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from string import Template

import aiohttp

from config import settings

logger = logging.getLogger(__name__)


class SMSOutreachService:
    """
    Send SMS to scraped businesses.
    
    Supports:
    - Twilio: International SMS provider
    - Fast2SMS: India-focused SMS provider
    
    Template variables:
    - {name}: Business name
    - {phone}: Business phone
    - {address}: Business address
    """
    
    def __init__(self, provider: str = None):
        """
        Initialize SMS service.
        
        Args:
            provider: SMS provider to use ("twilio" or "fast2sms")
        """
        self.provider = provider or settings.SMS_PROVIDER
        
        # Provider configurations
        self.twilio_config = {
            'account_sid': settings.TWILIO_ACCOUNT_SID,
            'auth_token': settings.TWILIO_AUTH_TOKEN,
            'from_number': settings.TWILIO_PHONE_NUMBER,
            'api_url': 'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
        }
        
        self.fast2sms_config = {
            'api_key': settings.FAST2SMS_API_KEY,
            'sender_id': settings.FAST2SMS_SENDER_ID or 'FSTSMS',
            'api_url': 'https://www.fast2sms.com/dev/bulkV2'
        }
    
    def _validate_phone(self, phone: str) -> Optional[str]:
        """
        Validate and normalize phone number.
        
        Args:
            phone: Raw phone number
            
        Returns:
            Cleaned phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Remove leading +
        if cleaned.startswith('+'):
            cleaned = cleaned[1:]
        
        # Basic validation: should be 10-15 digits
        if len(cleaned) < 10 or len(cleaned) > 15:
            return None
        
        return cleaned
    
    def _format_message(
        self,
        template: str,
        business: Dict[str, Any]
    ) -> str:
        """
        Format message template with business data.
        
        Args:
            template: Message template with {variable} placeholders
            business: Business data dictionary
            
        Returns:
            Formatted message
        """
        # Create substitution dict with defaults
        substitutions = {
            'name': business.get('name', 'Business'),
            'phone': business.get('phone', ''),
            'address': business.get('address', ''),
            'website': business.get('website', ''),
            'rating': str(business.get('rating', '')),
            'category': business.get('category', '')
        }
        
        try:
            # Use safe substitution (won't raise on missing keys)
            t = Template(template.replace('{', '${'))
            return t.safe_substitute(substitutions)
        except Exception:
            # Fallback: simple replace
            message = template
            for key, value in substitutions.items():
                message = message.replace(f'{{{key}}}', str(value))
            return message
    
    async def send_sms_single(
        self,
        phone: str,
        message: str,
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Send single SMS message.
        
        Args:
            phone: Recipient phone number
            message: Message content
            provider: Provider to use (default: configured provider)
            
        Returns:
            Dictionary with send status
        """
        provider = provider or self.provider
        
        # Validate phone
        cleaned_phone = self._validate_phone(phone)
        if not cleaned_phone:
            return {
                'success': False,
                'phone': phone,
                'error': 'Invalid phone number'
            }
        
        if provider == 'twilio':
            return await self._send_twilio(cleaned_phone, message)
        elif provider == 'fast2sms':
            return await self._send_fast2sms(cleaned_phone, message)
        else:
            return {
                'success': False,
                'phone': phone,
                'error': f'Unknown provider: {provider}'
            }
    
    async def _send_twilio(
        self,
        phone: str,
        message: str
    ) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        if not all([
            self.twilio_config['account_sid'],
            self.twilio_config['auth_token'],
            self.twilio_config['from_number']
        ]):
            return {
                'success': False,
                'phone': phone,
                'error': 'Twilio not configured'
            }
        
        try:
            url = self.twilio_config['api_url'].format(
                sid=self.twilio_config['account_sid']
            )
            
            # Ensure phone has country code
            if not phone.startswith('+'):
                phone = f'+{phone}'
            
            data = {
                'To': phone,
                'From': self.twilio_config['from_number'],
                'Body': message
            }
            
            auth = aiohttp.BasicAuth(
                self.twilio_config['account_sid'],
                self.twilio_config['auth_token']
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=data,
                    auth=auth
                ) as response:
                    result = await response.json()
                    
                    if response.status in [200, 201]:
                        logger.info(f"SMS sent to {phone} via Twilio")
                        return {
                            'success': True,
                            'phone': phone,
                            'message_sid': result.get('sid'),
                            'provider': 'twilio'
                        }
                    else:
                        error_msg = result.get('message', 'Unknown error')
                        logger.error(f"Twilio error for {phone}: {error_msg}")
                        return {
                            'success': False,
                            'phone': phone,
                            'error': error_msg,
                            'provider': 'twilio'
                        }
                        
        except Exception as e:
            logger.error(f"Twilio exception for {phone}: {e}")
            return {
                'success': False,
                'phone': phone,
                'error': str(e),
                'provider': 'twilio'
            }
    
    async def _send_fast2sms(
        self,
        phone: str,
        message: str
    ) -> Dict[str, Any]:
        """Send SMS via Fast2SMS (India)"""
        if not self.fast2sms_config['api_key']:
            return {
                'success': False,
                'phone': phone,
                'error': 'Fast2SMS not configured'
            }
        
        try:
            # Fast2SMS expects 10-digit Indian numbers
            # Remove country code if present
            if phone.startswith('91') and len(phone) == 12:
                phone = phone[2:]
            
            headers = {
                'authorization': self.fast2sms_config['api_key'],
                'Content-Type': 'application/json'
            }
            
            data = {
                'route': 'q',  # Quick SMS route
                'message': message,
                'language': 'english',
                'flash': 0,
                'numbers': phone
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.fast2sms_config['api_url'],
                    json=data,
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if result.get('return'):
                        logger.info(f"SMS sent to {phone} via Fast2SMS")
                        return {
                            'success': True,
                            'phone': phone,
                            'request_id': result.get('request_id'),
                            'provider': 'fast2sms'
                        }
                    else:
                        error_msg = result.get('message', 'Unknown error')
                        logger.error(f"Fast2SMS error for {phone}: {error_msg}")
                        return {
                            'success': False,
                            'phone': phone,
                            'error': error_msg,
                            'provider': 'fast2sms'
                        }
                        
        except Exception as e:
            logger.error(f"Fast2SMS exception for {phone}: {e}")
            return {
                'success': False,
                'phone': phone,
                'error': str(e),
                'provider': 'fast2sms'
            }
    
    async def send_sms_batch(
        self,
        results: List[Dict[str, Any]],
        message_template: str,
        provider: str = None,
        max_concurrent: int = 5,
        delay_between: float = 0.5
    ) -> Dict[str, Any]:
        """
        Send SMS to multiple businesses.
        
        Args:
            results: List of business dictionaries
            message_template: Message template with {variable} placeholders
            provider: Provider to use
            max_concurrent: Max concurrent sends
            delay_between: Delay between sends (rate limiting)
            
        Returns:
            Summary dictionary with success/failure counts
        """
        provider = provider or self.provider
        
        sent_results = []
        success_count = 0
        failure_count = 0
        skipped_count = 0
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def send_with_rate_limit(business: Dict):
            nonlocal success_count, failure_count, skipped_count
            
            async with semaphore:
                phone = business.get('phone')
                
                if not phone:
                    skipped_count += 1
                    return {
                        'business': business.get('name'),
                        'success': False,
                        'error': 'No phone number'
                    }
                
                message = self._format_message(message_template, business)
                result = await self.send_sms_single(phone, message, provider)
                
                if result['success']:
                    success_count += 1
                else:
                    failure_count += 1
                
                # Add business name to result
                result['business'] = business.get('name')
                
                # Rate limiting delay
                await asyncio.sleep(delay_between)
                
                return result
        
        # Create tasks for all businesses
        tasks = [send_with_rate_limit(business) for business in results]
        
        # Execute all tasks
        sent_results = await asyncio.gather(*tasks)
        
        summary = {
            'total': len(results),
            'success': success_count,
            'failed': failure_count,
            'skipped': skipped_count,
            'provider': provider,
            'results': sent_results
        }
        
        logger.info(
            f"SMS batch complete: {success_count} sent, "
            f"{failure_count} failed, {skipped_count} skipped"
        )
        
        return summary
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Check if SMS providers are configured"""
        return {
            'current_provider': self.provider,
            'twilio': {
                'configured': all([
                    self.twilio_config['account_sid'],
                    self.twilio_config['auth_token'],
                    self.twilio_config['from_number']
                ]),
                'from_number': self.twilio_config['from_number'] or 'Not set'
            },
            'fast2sms': {
                'configured': bool(self.fast2sms_config['api_key']),
                'sender_id': self.fast2sms_config['sender_id']
            }
        }


# Global instance for shared use
sms_service = SMSOutreachService()
