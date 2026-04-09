"""Tests for the CLI interface."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from envoy.cli import EnvoyCLI
from envoy.env_file import EnvFile


class TestEnvoyCLI:
    """Test suite for EnvoyCLI."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def cli(self):
        """Create a CLI instance."""
        return EnvoyCLI()

    def test_cli_no_command_shows_help(self, cli, capsys):
        """Test that running without a command shows help."""
        result = cli.run([])
        assert result == 1
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()

    @patch('envoy.cli.getpass.getpass')
    def test_push_command(self, mock_getpass, cli, temp_dir):
        """Test push command creates encrypted storage."""
        mock_getpass.return_value = "test_password"
        
        # Create a test .env file
        env_file_path = os.path.join(temp_dir, ".env")
        storage_dir = os.path.join(temp_dir, ".envoy")
        
        env_file = EnvFile(env_file_path)
        env_file.write({"TEST_VAR": "test_value"})
        
        # Run push command
        result = cli.run([
            "push", "test-env",
            "--env-file", env_file_path,
            "--storage-dir", storage_dir
        ])
        
        assert result == 0
        assert os.path.exists(os.path.join(storage_dir, "test-env.enc"))

    @patch('envoy.cli.getpass.getpass')
    def test_pull_command(self, mock_getpass, cli, temp_dir):
        """Test pull command retrieves encrypted data."""
        mock_getpass.return_value = "test_password"
        
        # Setup: push first
        env_file_path = os.path.join(temp_dir, ".env")
        pulled_file_path = os.path.join(temp_dir, ".env.pulled")
        storage_dir = os.path.join(temp_dir, ".envoy")
        
        env_file = EnvFile(env_file_path)
        env_file.write({"TEST_VAR": "test_value", "ANOTHER": "value2"})
        
        cli.run(["push", "test-env", "--env-file", env_file_path, "--storage-dir", storage_dir])
        
        # Now pull to a different file
        result = cli.run([
            "pull", "test-env",
            "--env-file", pulled_file_path,
            "--storage-dir", storage_dir
        ])
        
        assert result == 0
        pulled_env = EnvFile(pulled_file_path)
        data = pulled_env.read()
        assert data["TEST_VAR"] == "test_value"
        assert data["ANOTHER"] == "value2"

    def test_list_command_empty(self, cli, temp_dir, capsys):
        """Test list command with no stored environments."""
        storage_dir = os.path.join(temp_dir, ".envoy")
        result = cli.run(["list", "--storage-dir", storage_dir])
        
        assert result == 0
        captured = capsys.readouterr()
        assert "No stored environments" in captured.out

    @patch('envoy.cli.getpass.getpass')
    def test_list_command_with_items(self, mock_getpass, cli, temp_dir, capsys):
        """Test list command with stored environments."""
        mock_getpass.return_value = "test_password"
        
        env_file_path = os.path.join(temp_dir, ".env")
        storage_dir = os.path.join(temp_dir, ".envoy")
        
        env_file = EnvFile(env_file_path)
        env_file.write({"VAR": "value"})
        
        # Push multiple environments
        cli.run(["push", "dev", "--env-file", env_file_path, "--storage-dir", storage_dir])
        cli.run(["push", "prod", "--env-file", env_file_path, "--storage-dir", storage_dir])
        
        result = cli.run(["list", "--storage-dir", storage_dir])
        
        assert result == 0
        captured = capsys.readouterr()
        assert "dev" in captured.out
        assert "prod" in captured.out

    @patch('envoy.cli.getpass.getpass')
    def test_delete_command(self, mock_getpass, cli, temp_dir):
        """Test delete command removes stored environment."""
        mock_getpass.return_value = "test_password"
        
        env_file_path = os.path.join(temp_dir, ".env")
        storage_dir = os.path.join(temp_dir, ".envoy")
        
        env_file = EnvFile(env_file_path)
        env_file.write({"VAR": "value"})
        
        # Push and verify it exists
        cli.run(["push", "test-env", "--env-file", env_file_path, "--storage-dir", storage_dir])
        assert os.path.exists(os.path.join(storage_dir, "test-env.enc"))
        
        # Delete and verify it's gone
        result = cli.run(["delete", "test-env", "--storage-dir", storage_dir])
        assert result == 0
        assert not os.path.exists(os.path.join(storage_dir, "test-env.enc"))
