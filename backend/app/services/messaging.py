import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from app.utils.loggers import logger
from app.utils.rate_limiter import check_rate_limit
from twilio.rest import Client

twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

class MessageService:
    @staticmethod
    async def send_email(to: str, subject: str, body: str, is_html: bool = True):
        """Send email via SMTP with rate limiting"""
        if not check_rate_limit("smtp"):
            logger.warning(f"Rate limit exceeded for email to {to}")
            raise Exception("SMTP rate limit exceeded")
        
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = to
            msg['Subject'] = subject
            
            # Attach body with appropriate MIME type
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email successfully sent to {to}")
            return {"status": "sent", "email": to}
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed")
            raise Exception("SMTP authentication failed")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {str(e)}")
            raise Exception(f"SMTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected email error: {str(e)}")
            raise Exception(f"Email send failed: {str(e)}")

    @staticmethod
    async def send_whatsapp(to: str, body: str):
        """Send WhatsApp message via Twilio"""
        if not check_rate_limit("twilio_whatsapp"):
            logger.warning(f"Rate limit exceeded for WhatsApp to {to}")
            raise Exception("Twilio rate limit exceeded")
        
        try:
            message = twilio_client.messages.create(
                body=body,
                from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                to=f"whatsapp:{to}"
            )
            logger.info(f"WhatsApp message sent to {to} (SID: {message.sid})")
            return {"status": "sent", "message_sid": message.sid}
        except Exception as e:
            logger.error(f"WhatsApp send error to {to}: {str(e)}")
            raise Exception(f"WhatsApp send failed: {str(e)}")

    @staticmethod
    async def send_message(contact_method: str, recipient: str, message: str, subject: str = None):
        """Unified message sender"""
        if contact_method == "email":
            if not subject:
                subject = "Business Inquiry"
            return await MessageService.send_email(recipient, subject, message)
        elif contact_method == "whatsapp":
            return await MessageService.send_whatsapp(recipient, message)
        else:
            raise ValueError(f"Unsupported contact method: {contact_method}")