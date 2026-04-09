"""Tests for cryptographic utilities."""

import base64
import pytest
from envoy.crypto import EnvoyCrypto


class TestEnvoyCrypto:
    """Test suite for EnvoyCrypto class."""

    def test_encrypt_decrypt_basic(self):
        """Test basic encryption and decryption."""
        crypto = EnvoyCrypto("test_password")
        plaintext = "SECRET_KEY=my_secret_value"
        
        encrypted = crypto.encrypt(plaintext)
        decrypted = crypto.decrypt(encrypted)
        
        assert decrypted == plaintext
        assert encrypted != plaintext.encode()

    def test_encrypt_decrypt_multiline(self):
        """Test encryption of multiline .env content."""
        crypto = EnvoyCrypto("test_password")
        env_content = """DATABASE_URL=postgresql://localhost/db
API_KEY=abc123
DEBUG=true"""
        
        encrypted = crypto.encrypt(env_content)
        decrypted = crypto.decrypt(encrypted)
        
        assert decrypted == env_content

    def test_different_passwords_produce_different_results(self):
        """Test that different passwords produce different encrypted results."""
        plaintext = "SECRET=value"
        
        crypto1 = EnvoyCrypto("password1")
        crypto2 = EnvoyCrypto("password2")
        
        encrypted1 = crypto1.encrypt(plaintext)
        encrypted2 = crypto2.encrypt(plaintext)
        
        assert encrypted1 != encrypted2

    def test_same_password_with_salt_decrypts(self):
        """Test that same password with saved salt can decrypt."""
        plaintext = "API_KEY=secret123"
        password = "my_password"
        
        crypto1 = EnvoyCrypto(password)
        salt = crypto1.salt
        encrypted = crypto1.encrypt(plaintext)
        
        # Create new instance with same password and salt
        crypto2 = EnvoyCrypto(password, salt=salt)
        decrypted = crypto2.decrypt(encrypted)
        
        assert decrypted == plaintext

    def test_encrypt_env_file(self):
        """Test complete .env file encryption."""
        crypto = EnvoyCrypto("test_password")
        env_content = "DATABASE_URL=postgres://localhost\nAPI_KEY=xyz"
        
        result = crypto.encrypt_env_file(env_content)
        
        assert 'data' in result
        assert 'salt' in result
        assert isinstance(result['data'], str)
        assert isinstance(result['salt'], str)

    def test_decrypt_env_file(self):
        """Test complete .env file decryption."""
        password = "test_password"
        env_content = "SECRET=value123"
        
        crypto1 = EnvoyCrypto(password)
        encrypted_result = crypto1.encrypt_env_file(env_content)
        
        # Decrypt with new instance using same salt
        salt = base64.b64decode(encrypted_result['salt'])
        crypto2 = EnvoyCrypto(password, salt=salt)
        decrypted = crypto2.decrypt_env_file(encrypted_result['data'])
        
        assert decrypted == env_content

    def test_wrong_password_fails_decryption(self):
        """Test that wrong password fails to decrypt."""
        crypto1 = EnvoyCrypto("correct_password")
        encrypted = crypto1.encrypt("SECRET=value")
        
        crypto2 = EnvoyCrypto("wrong_password", salt=crypto1.salt)
        
        with pytest.raises(Exception):
            crypto2.decrypt(encrypted)
