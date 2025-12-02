"""
AES Encryption Utility for Sensitive Data at Rest
Uses Fernet (AES-128-CBC with HMAC) for symmetric encryption
"""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from decouple import config
import base64
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service class for encrypting/decrypting sensitive data using AES.
    Fernet guarantees that data encrypted using it cannot be 
    manipulated or read without the key.
    """
    
    _instance = None
    _fernet = None
    
    def __new__(cls):
        """Singleton pattern to reuse the same Fernet instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_fernet()
        return cls._instance
    
    def _initialize_fernet(self):
        """Initialize Fernet with the encryption key from settings"""
        try:
            encryption_key = config('ENCRYPTION_KEY')
            # Ensure the key is bytes
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            self._fernet = Fernet(encryption_key)
            logger.info("Encryption service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise ValueError(
                "Invalid ENCRYPTION_KEY. Generate one using: "
                "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
            )
    
    def encrypt(self, plain_text: str) -> str:
        """
        Encrypt a plain text string.
        
        Args:
            plain_text: The string to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        if not plain_text:
            return plain_text
            
        if not isinstance(plain_text, str):
            plain_text = str(plain_text)
        
        try:
            # Encode to bytes, encrypt, then decode to string for storage
            encrypted_bytes = self._fernet.encrypt(plain_text.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Failed to encrypt data")
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            encrypted_text: The encrypted string to decrypt
            
        Returns:
            Original plain text string
        """
        if not encrypted_text:
            return encrypted_text
            
        try:
            # Encode to bytes, decrypt, then decode to string
            decrypted_bytes = self._fernet.decrypt(encrypted_text.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            logger.warning("Failed to decrypt - invalid token (data may not be encrypted)")
            # Return as-is if it's not encrypted (for backward compatibility)
            return encrypted_text
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_text
    
    def is_encrypted(self, text: str) -> bool:
        """
        Check if a string appears to be encrypted.
        Fernet tokens start with 'gAAAAA'
        """
        if not text or not isinstance(text, str):
            return False
        return text.startswith('gAAAAA')


# Create a singleton instance for easy import
encryption_service = EncryptionService()


def encrypt_field(value: str) -> str:
    """Convenience function to encrypt a value"""
    return encryption_service.encrypt(value)


def decrypt_field(value: str) -> str:
    """Convenience function to decrypt a value"""
    return encryption_service.decrypt(value)