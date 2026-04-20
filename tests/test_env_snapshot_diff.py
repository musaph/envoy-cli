"""Tests for env_snapshot_diff module."""
import pytest
from envoy.snapshot import Snapshot
from envoy.env_snapshot_diff import SnapshotDiffer, SnapshotDiffEntry, SnapshotDiffResult


@pytest.fixture
def differ():
    return SnapshotDiffer()


@pytest.fixture
def old_snap():
    return Snapshot(vars={"A": "1", "B": "2", "C": "3"}, label="v1")


@pytest.fixture
def new_snap():
    return Snapshot(vars={"A": "1", "B": "99", "D": "4"}, label="v2")


class TestSnapshotDiffEntry:
    def test_repr_contains_key_and_status(self):
        e = SnapshotDiffEntry(key="FOO", status="added", new_value="bar")
        assert "FOO" in repr(e)
        assert "added" in repr(e)


class TestSnapshotDiffResult:
    def test_repr_contains_counts(self):
        r = SnapshotDiffResult()
        assert "added=0" in repr(r)
        assert "removed=0" in repr(r)

    def test_has_diff_false_when_all_unchanged(self):
        e = SnapshotDiffEntry(key="X", status="unchanged", old_value="1", new_value="1")
        r = SnapshotDiffResult(entries=[e])
        assert not r.has_diff()

    def test_has_diff_true_when_changed(self):
        e = SnapshotDiffEntry(key="X", status="changed", old_value="1", new_value="2")
        r = SnapshotDiffResult(entries=[e])
        assert r.has_diff()


class TestSnapshotDiffer:
    def test_added_key_detected(self, differ, old_snap, new_snap):
        result = differ.diff(old_snap, new_snap)
        keys = {e.key for e in result.added()}
        assert "D" in keys

    def test_removed_key_detected(self, differ, old_snap, new_snap):
        result = differ.diff(old_snap, new_snap)
        keys = {e.key for e in result.removed()}
        assert "C" in keys

    def test_changed_key_detected(self, differ, old_snap, new_snap):
        result = differ.diff(old_snap, new_snap)
        changed = {e.key: e for e in result.changed()}
        assert "B" in changed
        assert changed["B"].old_value == "2"
        assert changed["B"].new_value == "99"

    def test_unchanged_key_detected(self, differ, old_snap, new_snap):
        result = differ.diff(old_snap, new_snap)
        keys = {e.key for e in result.unchanged()}
        assert "A" in keys

    def test_identical_snapshots_no_diff(self, differ):
        snap = Snapshot(vars={"X": "1", "Y": "2"}, label="same")
        result = differ.diff(snap, snap)
        assert not result.has_diff()
        assert len(result.unchanged()) == 2

    def test_labels_propagated(self, differ, old_snap, new_snap):
        result = differ.diff(old_snap, new_snap)
        assert result.old_label == "v1"
        assert result.new_label == "v2"

    def test_entries_sorted_by_key(self, differ):
        a = Snapshot(vars={"Z": "1", "A": "2"})
        b = Snapshot(vars={"Z": "1", "A": "2"})
        result = differ.diff(a, b)
        keys = [e.key for e in result.entries]
        assert keys == sorted(keys)
