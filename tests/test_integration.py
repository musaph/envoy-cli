"""Integration tests for Envoy CLI."""

import pytest
from pathlib import Path
from envoy.config import EnvoyConfig
from envoy.storage import LocalFileStorage
from envoy.remote import RemoteEnvManager
from envoy.env_file import EnvFile
from envoy.crypto import EnvoyCrypto


class TestEnvoyIntegration:
    """Integration tests combining multiple components."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for tests."""
        return tmp_path

    @pytest.fixture
    def config(self, temp_dir):
        """Create config with temp directory."""
        config_dir = temp_dir / ".envoy"
        return EnvoyConfig(config_dir=config_dir)

    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage backend."""
        storage_path = temp_dir / "storage"
        return LocalFileStorage(str(storage_path))

    def test_config_storage_integration(self, config, temp_dir):
        """Test config and storage work together."""
        storage_path = str(temp_dir / "custom_storage")
        config.set_storage('local', storage_path)
        
        # Create storage using config values
        storage = LocalFileStorage(config.get_storage_path())
        
        # Save and load data
        storage.save('test_key', b'test_data')
        loaded = storage.load('test_key')
        
        assert loaded == b'test_data'

    def test_full_push_pull_workflow(self, temp_dir, storage):
        """Test complete push and pull workflow."""
        # Create env file
        env_path = temp_dir / ".env"
        env_content = "API_KEY=secret123\nDB_HOST=localhost"
        env_path.write_text(env_content)
        
        # Create remote manager
        password = "test_password"
        remote = RemoteEnvManager(storage, password)
        
        # Push env file
        remote.push("production", str(env_path))
        
        # Pull to different location
        pull_path = temp_dir / ".env.pulled"
        remote.pull("production", str(pull_path))
        
        # Verify content matches
        assert pull_path.read_text() == env_content

    def test_config_persists_across_instances(self, temp_dir):
        """Test configuration persists across instances."""
        config_dir = temp_dir / ".envoy"
        
        # First instance sets values
        config1 = EnvoyConfig(config_dir=config_dir)
        config1.set('storage_type', 's3')
        config1.set('storage_path', '/bucket/path')
        
        # Second instance should load same values
        config2 = EnvoyConfig(config_dir=config_dir)
        assert config2.get('storage_type') == 's3'
        assert config2.get('storage_path') == '/bucket/path'

    def test_multiple_environments_in_storage(self, storage):
        """Test storing multiple environments."""
        password = "test_password"
        remote = RemoteEnvManager(storage, password)
        
        # Create multiple env files
        environments = {
            'dev': 'ENV=dev\nDEBUG=true',
            'staging': 'ENV=staging\nDEBUG=false',
            'production': 'ENV=production\nDEBUG=false'
        }
        
        # Push all environments
        for env_name, content in environments.items():
            env_file = Path(f"/tmp/test_{env_name}.env")
            env_file.write_text(content)
            remote.push(env_name, str(env_file))
            env_file.unlink()
        
        # Verify all environments are listed
        env_list = remote.list_environments()
        assert set(env_list) == {'dev', 'staging', 'production'}

    def test_crypto_with_env_file_roundtrip(self, temp_dir):
        """Test encryption/decryption with actual env file content."""
        # Create env file with various formats
        env_content = '''# Database config
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD="complex!@#$%password"

# API Keys
API_KEY=abc123xyz
MULTILINE="line1
line2
line3"
'''
        
        crypto = EnvoyCrypto("test_password")
        
        # Encrypt and decrypt
        encrypted = crypto.encrypt(env_content)
        decrypted = crypto.decrypt(encrypted)
        
        assert decrypted == env_content
