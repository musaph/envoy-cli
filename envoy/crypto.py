"""Cryptographic utilities for encrypting and decrypting .env files."""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class EnvoyCrypto:
    """Handles encryption and decryption of environment variables."""

    def __init__(self, password: str, salt: bytes = None):
        """
        Initialize crypto handler with password.
        
        Args:
            password: Master password for encryption/decryption
            salt: Optional salt for key derivation (generated if not provided)
        """
        self.salt = salt or os.urandom(16)
        self.key = self._derive_key(password, self.salt)
        self.cipher = Fernet(self.key)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt plaintext string."""
        return self.cipher.encrypt(plaintext.encode())

    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt ciphertext to string."""
        return self.cipher.decrypt(ciphertext).decode()

    def encrypt_env_file(self, content: str) -> dict:
        """
        Encrypt .env file content.
        
        Returns:
            Dictionary with encrypted data and salt
        """
        encrypted = self.encrypt(content)
        return {
            'data': base64.b64encode(encrypted).decode(),
            'salt': base64.b64encode(self.salt).decode()
        }

    def decrypt_env_file(self, encrypted_data: str) -> str:
        """
        Decrypt .env file content.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted .env file content
        """
        ciphertext = base64.b64decode(encrypted_data)
        return self.decrypt(ciphertext)
