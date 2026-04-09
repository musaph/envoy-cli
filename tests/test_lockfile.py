"""Tests for envoy.lockfile."""

import pytest
from pathlib import Path
from envoy.lockfile import LockEntry, Lockfile, LOCKFILE_NAME


# ---------------------------------------------------------------------------
# LockEntry
# ---------------------------------------------------------------------------

class TestLockEntry:
    def test_checksum_is_sha256(self):
        cs = LockEntry.compute_checksum("secret")
        import hashlib
        assert cs == hashlib.sha256(b"secret").hexdigest()

    def test_roundtrip(self):
        entry = LockEntry(key="DB_PASS", checksum=LockEntry.compute_checksum("hunter2"))
        assert LockEntry.from_dict(entry.to_dict()) == entry


# ---------------------------------------------------------------------------
# Lockfile
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def sample_vars():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123"}


class TestLockfile:
    def test_update_creates_entries(self, sample_vars):
        lf = Lockfile(profile="dev")
        lf.update(sample_vars)
        assert set(lf.entries) == set(sample_vars)

    def test_is_stale_false_when_unchanged(self, sample_vars):
        lf = Lockfile(profile="dev")
        lf.update(sample_vars)
        assert not lf.is_stale(sample_vars)

    def test_is_stale_true_when_value_changed(self, sample_vars):
        lf = Lockfile(profile="dev")
        lf.update(sample_vars)
        modified = {**sample_vars, "DB_HOST": "remotehost"}
        assert lf.is_stale(modified)

    def test_is_stale_true_when_key_added(self, sample_vars):
        lf = Lockfile(profile="dev")
        lf.update(sample_vars)
        extra = {**sample_vars, "NEW_KEY": "value"}
        assert lf.is_stale(extra)

    def test_is_stale_true_when_key_removed(self, sample_vars):
        lf = Lockfile(profile="dev")
        lf.update(sample_vars)
        fewer = {k: v for k, v in sample_vars.items() if k != "API_KEY"}
        assert lf.is_stale(fewer)

    def test_save_creates_file(self, tmp_dir, sample_vars):
        lf = Lockfile(profile="dev")
        lf.update(sample_vars)
        path = lf.save(tmp_dir)
        assert path == tmp_dir / LOCKFILE_NAME
        assert path.exists()

    def test_load_returns_none_when_missing(self, tmp_dir):
        assert Lockfile.load(tmp_dir) is None

    def test_save_and_load_roundtrip(self, tmp_dir, sample_vars):
        lf = Lockfile(profile="staging")
        lf.update(sample_vars)
        lf.save(tmp_dir)

        loaded = Lockfile.load(tmp_dir)
        assert loaded is not None
        assert loaded.profile == "staging"
        assert set(loaded.entries) == set(sample_vars)
        assert not loaded.is_stale(sample_vars)

    def test_to_dict_roundtrip(self, sample_vars):
        lf = Lockfile(profile="prod")
        lf.update(sample_vars)
        restored = Lockfile.from_dict(lf.to_dict())
        assert restored.profile == lf.profile
        assert restored.entries == lf.entries
