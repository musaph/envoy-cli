"""Remote environment management functionality."""

from typing import Dict, Optional

from envoy.crypto import EnvoyCrypto
from envoy.parser import EnvParser
from envoy.storage import StorageBackend, LocalFileStorage


class RemoteEnvManager:
    """Manages remote encrypted environment storage and syncing."""

    def __init__(self, storage: Optional[StorageBackend] = None):
        """Initialize the remote environment manager.
        
        Args:
            storage: Storage backend to use. Defaults to LocalFileStorage.
        """
        self.storage = storage or LocalFileStorage()
        self.parser = EnvParser()

    def push(self, env_name: str, env_vars: Dict[str, str], password: str) -> None:
        """Encrypt and push environment variables to remote storage.
        
        Args:
            env_name: Name/identifier for the environment (e.g., 'production')
            env_vars: Dictionary of environment variables
            password: Password to encrypt the data with
        """
        # Serialize env vars to .env format
        env_content = self.parser.serialize(env_vars)
        
        # Encrypt the content
        crypto = EnvoyCrypto(password)
        encrypted_data = crypto.encrypt(env_content)
        
        # Save to storage
        self.storage.save(env_name, encrypted_data)

    def pull(self, env_name: str, password: str) -> Optional[Dict[str, str]]:
        """Pull and decrypt environment variables from remote storage.
        
        Args:
            env_name: Name/identifier for the environment
            password: Password to decrypt the data with
            
        Returns:
            Dictionary of environment variables or None if not found
            
        Raises:
            ValueError: If decryption fails (wrong password or corrupted data)
        """
        # Load encrypted data
        encrypted_data = self.storage.load(env_name)
        if encrypted_data is None:
            return None
        
        # Decrypt the content
        crypto = EnvoyCrypto(password)
        env_content = crypto.decrypt(encrypted_data)
        
        # Parse and return env vars
        return self.parser.parse(env_content)

    def delete(self, env_name: str) -> bool:
        """Delete an environment from remote storage.
        
        Args:
            env_name: Name/identifier for the environment
            
        Returns:
            True if deleted, False if not found
        """
        return self.storage.delete(env_name)

    def list_environments(self) -> list[str]:
        """List all stored environments.
        
        Returns:
            List of environment names
        """
        return self.storage.list_keys()

    def exists(self, env_name: str) -> bool:
        """Check if an environment exists in storage.
        
        Args:
            env_name: Name/identifier for the environment
            
        Returns:
            True if exists, False otherwise
        """
        return self.storage.load(env_name) is not None
