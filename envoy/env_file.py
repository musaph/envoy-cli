"""Environment file operations."""

import os
from pathlib import Path
from typing import Dict, Optional

from envoy.parser import EnvParser


class EnvFile:
    """Manage .env file operations."""

    def __init__(self, file_path: str = ".env"):
        """Initialize EnvFile.
        
        Args:
            file_path: Path to the .env file (default: .env)
        """
        self.file_path = Path(file_path)
        self.parser = EnvParser()

    def exists(self) -> bool:
        """Check if the .env file exists.
        
        Returns:
            True if file exists, False otherwise
        """
        return self.file_path.exists()

    def read(self) -> Dict[str, str]:
        """Read and parse the .env file.
        
        Returns:
            Dictionary of environment variables
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not self.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        content = self.file_path.read_text(encoding='utf-8')
        return self.parser.parse(content)

    def write(self, env_vars: Dict[str, str], backup: bool = True) -> None:
        """Write environment variables to the .env file.
        
        Args:
            env_vars: Dictionary of environment variables
            backup: Whether to create a backup before writing (default: True)
        """
        # Create backup if file exists and backup is requested
        if backup and self.exists():
            backup_path = self.file_path.with_suffix('.env.backup')
            backup_path.write_text(self.file_path.read_text(encoding='utf-8'))
        
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write serialized content
        content = self.parser.serialize(env_vars)
        self.file_path.write_text(content, encoding='utf-8')

    def update(self, updates: Dict[str, str]) -> Dict[str, str]:
        """Update specific variables in the .env file.
        
        Args:
            updates: Dictionary of variables to update
            
        Returns:
            Updated dictionary of all environment variables
        """
        # Read existing variables or start with empty dict
        try:
            env_vars = self.read()
        except FileNotFoundError:
            env_vars = {}
        
        # Apply updates
        env_vars.update(updates)
        
        # Write back
        self.write(env_vars)
        
        return env_vars

    def delete_keys(self, keys: list) -> Dict[str, str]:
        """Delete specific keys from the .env file.
        
        Args:
            keys: List of keys to delete
            
        Returns:
            Updated dictionary of environment variables
        """
        env_vars = self.read()
        
        for key in keys:
            env_vars.pop(key, None)
        
        self.write(env_vars)
        
        return env_vars
