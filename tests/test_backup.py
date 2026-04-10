"""Tests for EnvBackupManager."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envoy.backup import BackupEntry, EnvBackupManager


@pytest.fixture
def tmp_backup_dir(tmp_path):
    return str(tmp_path / "backups")


@pytest.fixture
def mgr(tmp_backup_dir):
    return EnvBackupManager(tmp_backup_dir)


SAMPLE_VARS = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc123"}


class TestBackupEntry:
    def test_to_dict_roundtrip(self):
        entry = BackupEntry(key="prod", timestamp="2024-01-01T00:00:00+00:00", vars=SAMPLE_VARS, note="test")
        assert BackupEntry.from_dict(entry.to_dict()) == entry

    def test_repr_contains_key(self):
        entry = BackupEntry(key="staging", timestamp="ts", vars={"A": "1"})
        assert "staging" in repr(entry)

    def test_default_note_is_empty(self):
        entry = BackupEntry(key="k", timestamp="t", vars={})
        assert entry.note == ""


class TestEnvBackupManager:
    def test_create_returns_entry(self, mgr):
        entry = mgr.create("prod", SAMPLE_VARS, note="initial")
        assert entry.key == "prod"
        assert entry.vars == SAMPLE_VARS
        assert entry.note == "initial"
        assert entry.timestamp

    def test_list_all_backups(self, mgr):
        mgr.create("prod", SAMPLE_VARS)
        mgr.create("staging", {"X": "1"})
        all_entries = mgr.list_backups()
        assert len(all_entries) == 2

    def test_list_filtered_by_key(self, mgr):
        mgr.create("prod", SAMPLE_VARS)
        mgr.create("prod", {"Y": "2"})
        mgr.create("staging", {"Z": "3"})
        prod_entries = mgr.list_backups(key="prod")
        assert len(prod_entries) == 2
        assert all(e.key == "prod" for e in prod_entries)

    def test_restore_returns_latest_by_default(self, mgr):
        mgr.create("prod", {"V": "1"})
        mgr.create("prod", {"V": "2"})
        entry = mgr.restore("prod")
        assert entry is not None
        assert entry.vars["V"] == "2"

    def test_restore_by_index(self, mgr):
        mgr.create("prod", {"V": "first"})
        mgr.create("prod", {"V": "second"})
        entry = mgr.restore("prod", index=0)
        assert entry.vars["V"] == "first"

    def test_restore_missing_key_returns_none(self, mgr):
        assert mgr.restore("nonexistent") is None

    def test_delete_removes_all_for_key(self, mgr):
        mgr.create("prod", SAMPLE_VARS)
        mgr.create("prod", SAMPLE_VARS)
        mgr.create("staging", {"A": "1"})
        removed = mgr.delete("prod")
        assert removed == 2
        assert mgr.list_backups(key="prod") == []
        assert len(mgr.list_backups(key="staging")) == 1

    def test_index_persists_across_instances(self, tmp_backup_dir):
        mgr1 = EnvBackupManager(tmp_backup_dir)
        mgr1.create("prod", SAMPLE_VARS, note="persisted")
        mgr2 = EnvBackupManager(tmp_backup_dir)
        entries = mgr2.list_backups(key="prod")
        assert len(entries) == 1
        assert entries[0].note == "persisted"
