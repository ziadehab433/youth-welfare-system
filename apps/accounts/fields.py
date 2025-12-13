"""
Custom Django Model Field for Encrypted Data
Automatically encrypts on save and decrypts on read
"""

from django.db import models
from .encryption import encrypt_field, decrypt_field, encryption_service


class EncryptedTextField(models.TextField):
    """
    A TextField that automatically encrypts data before saving
    and decrypts data when reading from the database.
    
    Uses AES encryption (Fernet) for secure storage of sensitive data.
    """
    
    description = "An encrypted TextField using AES encryption"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """
        Encrypt the value before saving to database.
        Called when saving to DB.
        """
        if value is None:
            return value
        
        # Don't double-encrypt
        if encryption_service.is_encrypted(value):
            return value
            
        return encrypt_field(value)
    
    def from_db_value(self, value, expression, connection):
        """
        Decrypt the value when reading from database.
        Called when loading from DB.
        """
        if value is None:
            return value
        return decrypt_field(value)
    
    def to_python(self, value):
        """
        Convert the value to Python string.
        Handles decryption for values that might be encrypted.
        """
        if value is None:
            return value
        
        if isinstance(value, str):
            # If it's encrypted, decrypt it
            if encryption_service.is_encrypted(value):
                return decrypt_field(value)
        
        return value


class EncryptedCharField(models.CharField):
    """
    A CharField that automatically encrypts data before saving
    and decrypts data when reading from the database.
    
    Note: Encrypted data is longer than original, so max_length 
    should be set higher (typically 255+ for short strings)
    """
    
    description = "An encrypted CharField using AES encryption"
    
    def __init__(self, *args, **kwargs):
        # Encrypted data is longer, ensure adequate max_length
        if 'max_length' in kwargs and kwargs['max_length'] < 255:
            kwargs['max_length'] = 255
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """Encrypt before saving"""
        if value is None:
            return value
        
        if encryption_service.is_encrypted(value):
            return value
            
        return encrypt_field(value)
    
    def from_db_value(self, value, expression, connection):
        """Decrypt when reading"""
        if value is None:
            return value
        return decrypt_field(value)
    
    def to_python(self, value):
        """Convert to Python, handling encrypted values"""
        if value is None:
            return value
        
        if isinstance(value, str) and encryption_service.is_encrypted(value):
            return decrypt_field(value)
        
        return value