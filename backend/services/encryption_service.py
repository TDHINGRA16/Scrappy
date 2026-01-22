"""
Encryption Service for Scrappy v2.0

Provides Fernet symmetric encryption for sensitive data (OAuth tokens).
All tokens are encrypted before database storage.
"""

from cryptography.fernet import Fernet, InvalidToken
import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service to encrypt and decrypt sensitive data (OAuth tokens) using Fernet symmetric encryption.

    Environment Variable Required:
        ENCRYPTION_KEY: Base64-encoded Fernet key (generate with: Fernet.generate_key())
    
    Usage:
        encryption_service = EncryptionService()
        
        # Encrypt credentials
        encrypted = encryption_service.encrypt_credentials({
            "access_token": "...",
            "refresh_token": "..."
        })
        
        # Decrypt credentials
        credentials = encryption_service.decrypt_credentials(encrypted)
    """

    def __init__(self):
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            # Generate a key for development (should be set in production)
            logger.warning("⚠️ ENCRYPTION_KEY not set. Generating temporary key for development.")
            logger.warning("   Set ENCRYPTION_KEY in .env for production use!")
            self._temp_key = Fernet.generate_key()
            self.cipher = Fernet(self._temp_key)
        else:
            try:
                self.cipher = Fernet(encryption_key.encode())
            except Exception as e:
                logger.error(f"Invalid ENCRYPTION_KEY format: {e}")
                raise ValueError("ENCRYPTION_KEY must be a valid Fernet key (base64-encoded 32 bytes)")

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credentials dictionary to encrypted string.

        Args:
            credentials: Dictionary containing access_token, refresh_token, etc.

        Returns:
            Encrypted string safe for database storage
        """
        try:
            credentials_json = json.dumps(credentials)
            encrypted_bytes = self.cipher.encrypt(credentials_json.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """
        Decrypt encrypted string back to credentials dictionary.

        Args:
            encrypted_credentials: Encrypted string from database

        Returns:
            Dictionary with decrypted credentials
            
        Raises:
            InvalidToken: If decryption fails (wrong key or corrupted data)
        """
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_credentials.encode('utf-8'))
            credentials_json = decrypted_bytes.decode('utf-8')
            return json.loads(credentials_json)
        except InvalidToken:
            logger.error("Decryption failed - invalid token or wrong key")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.
        
        Returns:
            Base64-encoded key string to store in ENCRYPTION_KEY env var
        """
        return Fernet.generate_key().decode('utf-8')


# Lazy singleton instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get singleton encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


# For convenience
encryption_service = get_encryption_service()
