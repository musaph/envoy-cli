"""Configuration management for Envoy CLI."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class EnvoyConfig:
    """Manages Envoy configuration settings."""

    DEFAULT_CONFIG_DIR = Path.home() / ".envoy"
    DEFAULT_CONFIG_FILE = "config.json"
    DEFAULT_STORAGE_TYPE = "local"
    DEFAULT_STORAGE_PATH = str(DEFAULT_CONFIG_DIR / "storage")

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Directory for storing configuration. Defaults to ~/.envoy
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_file = self.config_dir / self.DEFAULT_CONFIG_FILE
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = {}
        else:
            self._config = {}

    def _save_config(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self._config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
        self._save_config()

    def get_storage_type(self) -> str:
        """Get configured storage type."""
        return self.get('storage_type', self.DEFAULT_STORAGE_TYPE)

    def get_storage_path(self) -> str:
        """Get configured storage path."""
        return self.get('storage_path', self.DEFAULT_STORAGE_PATH)

    def set_storage(self, storage_type: str, storage_path: str) -> None:
        """Configure storage settings.

        Args:
            storage_type: Type of storage backend
            storage_path: Path for storage
        """
        self.set('storage_type', storage_type)
        self.set('storage_path', storage_path)

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()

    def clear(self) -> None:
        """Clear all configuration."""
        self._config = {}
        if self.config_file.exists():
            self.config_file.unlink()
