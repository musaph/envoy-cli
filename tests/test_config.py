"""Tests for configuration management."""

import json
import pytest
from pathlib import Path
from envoy.config import EnvoyConfig


class TestEnvoyConfig:
    """Test cases for EnvoyConfig class."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create a temporary config directory."""
        config_dir = tmp_path / ".envoy"
        config_dir.mkdir()
        return config_dir

    @pytest.fixture
    def config(self, temp_config_dir):
        """Create a config instance with temp directory."""
        return EnvoyConfig(config_dir=temp_config_dir)

    def test_config_initialization(self, config, temp_config_dir):
        """Test config initializes with correct directory."""
        assert config.config_dir == temp_config_dir
        assert config.config_file == temp_config_dir / "config.json"

    def test_set_and_get_value(self, config):
        """Test setting and getting configuration values."""
        config.set('test_key', 'test_value')
        assert config.get('test_key') == 'test_value'

    def test_get_nonexistent_key_returns_default(self, config):
        """Test getting nonexistent key returns default value."""
        assert config.get('nonexistent') is None
        assert config.get('nonexistent', 'default') == 'default'

    def test_config_persists_to_file(self, config, temp_config_dir):
        """Test configuration is saved to file."""
        config.set('persistent_key', 'persistent_value')
        
        config_file = temp_config_dir / "config.json"
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config['persistent_key'] == 'persistent_value'

    def test_config_loads_from_existing_file(self, temp_config_dir):
        """Test configuration loads from existing file."""
        config_file = temp_config_dir / "config.json"
        config_data = {'existing_key': 'existing_value'}
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = EnvoyConfig(config_dir=temp_config_dir)
        assert config.get('existing_key') == 'existing_value'

    def test_storage_type_default(self, config):
        """Test default storage type."""
        assert config.get_storage_type() == 'local'

    def test_storage_path_default(self, config, temp_config_dir):
        """Test default storage path."""
        default_path = str(temp_config_dir / "storage")
        # Since we're using a custom config_dir, check it returns the default
        storage_path = config.get_storage_path()
        assert storage_path == str(EnvoyConfig.DEFAULT_CONFIG_DIR / "storage")

    def test_set_storage_configuration(self, config):
        """Test setting storage configuration."""
        config.set_storage('s3', '/path/to/s3')
        assert config.get_storage_type() == 's3'
        assert config.get_storage_path() == '/path/to/s3'

    def test_get_all_returns_copy(self, config):
        """Test get_all returns a copy of config."""
        config.set('key1', 'value1')
        config.set('key2', 'value2')
        
        all_config = config.get_all()
        assert all_config == {'key1': 'value1', 'key2': 'value2'}
        
        # Modifying returned dict shouldn't affect original
        all_config['key3'] = 'value3'
        assert config.get('key3') is None

    def test_clear_removes_all_config(self, config):
        """Test clear removes all configuration."""
        config.set('key1', 'value1')
        config.set('key2', 'value2')
        
        config.clear()
        
        assert config.get_all() == {}
        assert not config.config_file.exists()

    def test_handles_corrupted_config_file(self, temp_config_dir):
        """Test handling of corrupted config file."""
        config_file = temp_config_dir / "config.json"
        
        with open(config_file, 'w') as f:
            f.write('invalid json content {')
        
        config = EnvoyConfig(config_dir=temp_config_dir)
        # Should initialize with empty config
        assert config.get_all() == {}
