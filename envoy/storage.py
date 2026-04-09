"""Storage backend interface and implementations for envoy."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save(self, key: str, data: str) -> None:
        """Save encrypted data to storage.
        
        Args:
            key: Identifier for the stored data (e.g., environment name)
            data: Encrypted data to store
        """
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[str]:
        """Load encrypted data from storage.
        
        Args:
            key: Identifier for the stored data
            
        Returns:
            Encrypted data or None if not found
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data from storage.
        
        Args:
            key: Identifier for the stored data
            
        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all stored keys.
        
        Returns:
            List of all stored keys
        """
        pass


class LocalFileStorage(StorageBackend):
    """Local file-based storage backend."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize local file storage.
        
        Args:
            storage_dir: Directory to store files. Defaults to ~/.envoy/storage
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".envoy" / "storage"
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"
        self._load_index()

    def _load_index(self) -> None:
        """Load the index of stored environments."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {}

    def _save_index(self) -> None:
        """Save the index of stored environments."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def save(self, key: str, data: str) -> None:
        """Save encrypted data to a local file."""
        file_path = self.storage_dir / f"{key}.enc"
        with open(file_path, 'w') as f:
            f.write(data)
        self.index[key] = str(file_path)
        self._save_index()

    def load(self, key: str) -> Optional[str]:
        """Load encrypted data from a local file."""
        file_path = self.storage_dir / f"{key}.enc"
        if not file_path.exists():
            return None
        with open(file_path, 'r') as f:
            return f.read()

    def delete(self, key: str) -> bool:
        """Delete a stored environment file."""
        file_path = self.storage_dir / f"{key}.enc"
        if not file_path.exists():
            return False
        file_path.unlink()
        if key in self.index:
            del self.index[key]
            self._save_index()
        return True

    def list_keys(self) -> list[str]:
        """List all stored environment keys."""
        return list(self.index.keys())
