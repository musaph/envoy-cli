"""Tests for EnvArchiveManager and ArchiveEntry."""
import pytest
from envoy.env_archive import ArchiveEntry, ArchiveResult, EnvArchiveManager


@pytest.fixture
def manager() -> EnvArchiveManager:
    return EnvArchiveManager()


@pytest.fixture
def sample_vars() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}


class TestArchiveEntry:
    def test_to_dict_roundtrip(self, sample_vars):
        entry = ArchiveEntry(label="v1", vars=sample_vars)
        restored = ArchiveEntry.from_dict(entry.to_dict())
        assert restored.label == entry.label
        assert restored.vars == entry.vars
        assert restored.checksum == entry.checksum

    def test_repr_contains_label(self, sample_vars):
        entry = ArchiveEntry(label="prod", vars=sample_vars)
        assert "prod" in repr(entry)

    def test_checksum_is_sha256_hex(self, sample_vars):
        entry = ArchiveEntry(label="x", vars=sample_vars)
        assert len(entry.checksum) == 64
        assert all(c in "0123456789abcdef" for c in entry.checksum)

    def test_different_vars_produce_different_checksums(self):
        e1 = ArchiveEntry(label="a", vars={"K": "1"})
        e2 = ArchiveEntry(label="a", vars={"K": "2"})
        assert e1.checksum != e2.checksum

    def test_same_vars_produce_same_checksum(self, sample_vars):
        e1 = ArchiveEntry(label="a", vars=sample_vars)
        e2 = ArchiveEntry(label="b", vars=sample_vars)
        assert e1.checksum == e2.checksum


class TestArchiveResult:
    def test_repr(self):
        r = ArchiveResult()
        assert "entries=0" in repr(r)
        assert "errors=0" in repr(r)


class TestEnvArchiveManager:
    def test_save_and_list(self, manager, sample_vars):
        manager.save("v1", sample_vars)
        entries = manager.list_entries()
        assert len(entries) == 1
        assert entries[0].label == "v1"

    def test_restore_returns_copy(self, manager, sample_vars):
        manager.save("v1", sample_vars)
        restored = manager.restore("v1")
        assert restored == sample_vars
        restored["NEW"] = "val"
        assert "NEW" not in manager.restore("v1")

    def test_restore_nonexistent_returns_none(self, manager):
        assert manager.restore("ghost") is None

    def test_restore_returns_latest_when_duplicate_labels(self, manager):
        manager.save("v1", {"A": "1"})
        manager.save("v1", {"A": "2"})
        assert manager.restore("v1") == {"A": "2"}

    def test_delete_existing_label(self, manager, sample_vars):
        manager.save("v1", sample_vars)
        result = manager.delete("v1")
        assert result is True
        assert manager.restore("v1") is None

    def test_delete_nonexistent_returns_false(self, manager):
        assert manager.delete("ghost") is False

    def test_to_dict_list_roundtrip(self, manager, sample_vars):
        manager.save("v1", sample_vars)
        manager.save("v2", {"X": "y"})
        data = manager.to_dict_list()
        new_mgr = EnvArchiveManager()
        new_mgr.load_from_dict_list(data)
        assert new_mgr.restore("v1") == sample_vars
        assert new_mgr.restore("v2") == {"X": "y"}

    def test_multiple_labels_independent(self, manager):
        manager.save("a", {"K": "1"})
        manager.save("b", {"K": "2"})
        assert manager.restore("a") == {"K": "1"}
        assert manager.restore("b") == {"K": "2"}
