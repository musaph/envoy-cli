"""Tests for the sync module."""

import pytest
from envoy.sync import EnvSyncManager, SyncAction, SyncDiff


class TestEnvSyncManager:
    """Test cases for EnvSyncManager."""

    def test_compare_identical_vars(self):
        """Test comparing identical local and remote variables."""
        sync = EnvSyncManager()
        local = {"KEY1": "value1", "KEY2": "value2"}
        remote = {"KEY1": "value1", "KEY2": "value2"}
        
        diffs = sync.compare(local, remote)
        
        assert len(diffs) == 2
        assert all(diff.action == SyncAction.NO_CHANGE for diff in diffs)

    def test_compare_remote_has_new_keys(self):
        """Test when remote has keys not in local."""
        sync = EnvSyncManager()
        local = {"KEY1": "value1"}
        remote = {"KEY1": "value1", "KEY2": "value2"}
        
        diffs = sync.compare(local, remote)
        
        assert len(diffs) == 2
        key2_diff = next(d for d in diffs if d.key == "KEY2")
        assert key2_diff.action == SyncAction.ADD
        assert key2_diff.local_value is None
        assert key2_diff.remote_value == "value2"

    def test_compare_local_has_new_keys(self):
        """Test when local has keys not in remote."""
        sync = EnvSyncManager()
        local = {"KEY1": "value1", "KEY2": "value2"}
        remote = {"KEY1": "value1"}
        
        diffs = sync.compare(local, remote)
        
        assert len(diffs) == 2
        key2_diff = next(d for d in diffs if d.key == "KEY2")
        assert key2_diff.action == SyncAction.DELETE
        assert key2_diff.local_value == "value2"
        assert key2_diff.remote_value is None

    def test_compare_conflicting_values(self):
        """Test when same key has different values."""
        sync = EnvSyncManager()
        local = {"KEY1": "local_value"}
        remote = {"KEY1": "remote_value"}
        
        diffs = sync.compare(local, remote)
        
        assert len(diffs) == 1
        assert diffs[0].action == SyncAction.CONFLICT
        assert diffs[0].local_value == "local_value"
        assert diffs[0].remote_value == "remote_value"

    def test_compare_mixed_scenario(self):
        """Test complex scenario with multiple diff types."""
        sync = EnvSyncManager()
        local = {
            "SAME": "value",
            "LOCAL_ONLY": "local",
            "CONFLICT": "local_val"
        }
        remote = {
            "SAME": "value",
            "REMOTE_ONLY": "remote",
            "CONFLICT": "remote_val"
        }
        
        diffs = sync.compare(local, remote)
        
        assert len(diffs) == 4
        actions = {diff.key: diff.action for diff in diffs}
        assert actions["SAME"] == SyncAction.NO_CHANGE
        assert actions["LOCAL_ONLY"] == SyncAction.DELETE
        assert actions["REMOTE_ONLY"] == SyncAction.ADD
        assert actions["CONFLICT"] == SyncAction.CONFLICT

    def test_merge_remote_strategy(self):
        """Test merge with remote strategy (remote wins)."""
        sync = EnvSyncManager()
        local = {"KEY1": "local", "KEY2": "local2"}
        remote = {"KEY1": "remote", "KEY3": "remote3"}
        
        merged = sync.merge(local, remote, strategy="remote")
        
        assert merged["KEY1"] == "remote"  # Remote wins
        assert merged["KEY2"] == "local2"  # Only in local
        assert merged["KEY3"] == "remote3"  # Only in remote

    def test_merge_local_strategy(self):
        """Test merge with local strategy (local wins)."""
        sync = EnvSyncManager()
        local = {"KEY1": "local", "KEY2": "local2"}
        remote = {"KEY1": "remote", "KEY3": "remote3"}
        
        merged = sync.merge(local, remote, strategy="local")
        
        assert merged["KEY1"] == "local"  # Local wins
        assert merged["KEY2"] == "local2"  # Only in local
        assert merged["KEY3"] == "remote3"  # Only in remote

    def test_merge_invalid_strategy(self):
        """Test merge with invalid strategy raises error."""
        sync = EnvSyncManager()
        local = {"KEY1": "value"}
        remote = {"KEY1": "value"}
        
        with pytest.raises(ValueError, match="Unknown merge strategy"):
            sync.merge(local, remote, strategy="invalid")

    def test_has_conflicts(self):
        """Test detecting conflicts in diffs."""
        sync = EnvSyncManager()
        
        no_conflicts = [
            SyncDiff("KEY1", SyncAction.NO_CHANGE, "val", "val"),
            SyncDiff("KEY2", SyncAction.ADD, None, "val")
        ]
        assert not sync.has_conflicts(no_conflicts)
        
        with_conflicts = [
            SyncDiff("KEY1", SyncAction.NO_CHANGE, "val", "val"),
            SyncDiff("KEY2", SyncAction.CONFLICT, "local", "remote")
        ]
        assert sync.has_conflicts(with_conflicts)

    def test_get_conflicts(self):
        """Test filtering only conflicts from diffs."""
        sync = EnvSyncManager()
        
        diffs = [
            SyncDiff("KEY1", SyncAction.NO_CHANGE, "val", "val"),
            SyncDiff("KEY2", SyncAction.CONFLICT, "local", "remote"),
            SyncDiff("KEY3", SyncAction.ADD, None, "val"),
            SyncDiff("KEY4", SyncAction.CONFLICT, "local2", "remote2")
        ]
        
        conflicts = sync.get_conflicts(diffs)
        
        assert len(conflicts) == 2
        assert all(c.action == SyncAction.CONFLICT for c in conflicts)
        assert conflicts[0].key == "KEY2"
        assert conflicts[1].key == "KEY4"
