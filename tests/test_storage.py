"""Tests for storage backends."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from envoy.storage import LocalFileStorage, StorageBackend


class TestLocalFileStorage:
    """Tests for LocalFileStorage backend."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory."""
        with TemporaryDirectory() as tmpdir:
            yield LocalFileStorage(storage_dir=Path(tmpdir))

    def test_save_and_load(self, temp_storage):
        """Test saving and loading data."""
        key = "production"
        data = "encrypted_data_here"
        
        temp_storage.save(key, data)
        loaded_data = temp_storage.load(key)
        
        assert loaded_data == data

    def test_load_nonexistent_key(self, temp_storage):
        """Test loading a key that doesn't exist."""
        result = temp_storage.load("nonexistent")
        assert result is None

    def test_delete_existing_key(self, temp_storage):
        """Test deleting an existing key."""
        key = "staging"
        data = "some_encrypted_data"
        
        temp_storage.save(key, data)
        assert temp_storage.load(key) == data
        
        result = temp_storage.delete(key)
        assert result is True
        assert temp_storage.load(key) is None

    def test_delete_nonexistent_key(self, temp_storage):
        """Test deleting a key that doesn't exist."""
        result = temp_storage.delete("nonexistent")
        assert result is False

    def test_list_keys_empty(self, temp_storage):
        """Test listing keys when storage is empty."""
        keys = temp_storage.list_keys()
        assert keys == []

    def test_list_keys_multiple(self, temp_storage):
        """Test listing multiple stored keys."""
        keys_to_save = ["production", "staging", "development"]
        
        for key in keys_to_save:
            temp_storage.save(key, f"data_for_{key}")
        
        stored_keys = temp_storage.list_keys()
        assert set(stored_keys) == set(keys_to_save)

    def test_overwrite_existing_key(self, temp_storage):
        """Test overwriting data for an existing key."""
        key = "production"
        original_data = "original_data"
        new_data = "new_data"
        
        temp_storage.save(key, original_data)
        assert temp_storage.load(key) == original_data
        
        temp_storage.save(key, new_data)
        assert temp_storage.load(key) == new_data

    def test_index_persistence(self):
        """Test that index persists across instances."""
        with TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            
            # Create first instance and save data
            storage1 = LocalFileStorage(storage_dir=storage_dir)
            storage1.save("test_key", "test_data")
            keys1 = storage1.list_keys()
            
            # Create second instance and verify data persists
            storage2 = LocalFileStorage(storage_dir=storage_dir)
            keys2 = storage2.list_keys()
            
            assert keys1 == keys2
            assert "test_key" in keys2
            assert storage2.load("test_key") == "test_data"

    def test_storage_directory_created(self):
        """Test that storage directory is created if it doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "nested" / "storage"
            assert not storage_dir.exists()
            
            storage = LocalFileStorage(storage_dir=storage_dir)
            assert storage_dir.exists()
            assert storage_dir.is_dir()
