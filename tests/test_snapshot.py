"""Tests for envoy.snapshot module."""

import json
import pathlib

import pytest

from envoy.snapshot import Snapshot, SnapshotManager


SAMPLE_VARS = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc123"}


# ---------------------------------------------------------------------------
# Snapshot dataclass
# ---------------------------------------------------------------------------

class TestSnapshot:
    def test_creation_sets_checksum(self):
        snap = Snapshot(label="v1", variables=SAMPLE_VARS)
        assert snap.checksum
        assert len(snap.checksum) == 16

    def test_same_vars_same_checksum(self):
        s1 = Snapshot(label="a", variables={"K": "V"})
        s2 = Snapshot(label="b", variables={"K": "V"})
        assert s1.checksum == s2.checksum

    def test_different_vars_different_checksum(self):
        s1 = Snapshot(label="a", variables={"K": "V1"})
        s2 = Snapshot(label="a", variables={"K": "V2"})
        assert s1.checksum != s2.checksum

    def test_to_dict_roundtrip(self):
        snap = Snapshot(label="prod", variables=SAMPLE_VARS)
        restored = Snapshot.from_dict(snap.to_dict())
        assert restored.label == snap.label
        assert restored.variables == snap.variables
        assert restored.checksum == snap.checksum
        assert restored.created_at == snap.created_at

    def test_repr_contains_label_and_count(self):
        snap = Snapshot(label="dev", variables=SAMPLE_VARS)
        r = repr(snap)
        assert "dev" in r
        assert str(len(SAMPLE_VARS)) in r


# ---------------------------------------------------------------------------
# SnapshotManager
# ---------------------------------------------------------------------------

@pytest.fixture
def manager():
    return SnapshotManager()


class TestSnapshotManager:
    def test_capture_returns_snapshot(self, manager):
        snap = manager.capture("v1", SAMPLE_VARS)
        assert isinstance(snap, Snapshot)
        assert snap.label == "v1"

    def test_list_snapshots_empty_initially(self, manager):
        assert manager.list_snapshots() == []

    def test_list_snapshots_after_capture(self, manager):
        manager.capture("v1", SAMPLE_VARS)
        manager.capture("v2", {"A": "1"})
        assert len(manager.list_snapshots()) == 2

    def test_get_returns_latest_for_label(self, manager):
        manager.capture("env", {"X": "1"})
        manager.capture("env", {"X": "2"})
        snap = manager.get("env")
        assert snap.variables["X"] == "2"

    def test_get_nonexistent_returns_none(self, manager):
        assert manager.get("ghost") is None

    def test_delete_existing_label(self, manager):
        manager.capture("temp", {"T": "1"})
        removed = manager.delete("temp")
        assert removed is True
        assert manager.get("temp") is None

    def test_delete_nonexistent_returns_false(self, manager):
        assert manager.delete("nope") is False

    def test_capture_does_not_mutate_original(self, manager):
        original = {"K": "V"}
        manager.capture("snap", original)
        original["K"] = "CHANGED"
        assert manager.get("snap").variables["K"] == "V"

    def test_persist_and_reload(self, tmp_path):
        store = str(tmp_path / "snaps.json")
        m1 = SnapshotManager(store_path=store)
        m1.capture("release", SAMPLE_VARS)

        m2 = SnapshotManager(store_path=store)
        snap = m2.get("release")
        assert snap is not None
        assert snap.variables == SAMPLE_VARS

    def test_delete_persists_to_disk(self, tmp_path):
        store = str(tmp_path / "snaps.json")
        m1 = SnapshotManager(store_path=store)
        m1.capture("old", {"A": "1"})
        m1.delete("old")

        m2 = SnapshotManager(store_path=store)
        assert m2.get("old") is None
