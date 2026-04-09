"""Integration tests for sync functionality."""

import pytest
from envoy.sync import EnvSyncManager, SyncAction
from envoy.diff import DiffFormatter
from envoy.parser import EnvParser


class TestSyncIntegration:
    """Integration tests combining sync, diff, and parser."""

    def test_sync_workflow_with_parser(self):
        """Test complete sync workflow using parser."""
        # Parse local .env content
        local_content = """DATABASE_URL=postgres://localhost
API_KEY=local_key
DEBUG=true"""
        
        # Parse remote .env content
        remote_content = """DATABASE_URL=postgres://remote
API_KEY=local_key
NEW_VAR=new_value"""
        
        parser = EnvParser()
        local_vars = parser.parse(local_content)
        remote_vars = parser.parse(remote_content)
        
        # Compare
        sync = EnvSyncManager()
        diffs = sync.compare(local_vars, remote_vars)
        
        # Verify diffs
        assert len(diffs) == 4
        actions = {d.key: d.action for d in diffs}
        assert actions["DATABASE_URL"] == SyncAction.CONFLICT
        assert actions["API_KEY"] == SyncAction.NO_CHANGE
        assert actions["DEBUG"] == SyncAction.DELETE
        assert actions["NEW_VAR"] == SyncAction.ADD

    def test_merge_and_serialize(self):
        """Test merging and serializing back to .env format."""
        local_vars = {"KEY1": "local", "KEY2": "value2"}
        remote_vars = {"KEY1": "remote", "KEY3": "value3"}
        
        sync = EnvSyncManager()
        merged = sync.merge(local_vars, remote_vars, strategy="remote")
        
        # Serialize merged result
        parser = EnvParser()
        serialized = parser.serialize(merged)
        
        # Verify serialized output
        assert "KEY1=remote" in serialized
        assert "KEY2=value2" in serialized
        assert "KEY3=value3" in serialized

    def test_diff_formatter_with_real_diffs(self):
        """Test diff formatter with real sync diffs."""
        local_vars = {"KEY1": "local", "KEY2": "same"}
        remote_vars = {"KEY2": "same", "KEY3": "remote"}
        
        sync = EnvSyncManager()
        diffs = sync.compare(local_vars, remote_vars)
        
        formatter = DiffFormatter(use_color=False)
        output = formatter.format_all(diffs, show_unchanged=True)
        
        # Verify output contains expected information
        assert "KEY1" in output
        assert "KEY2" in output
        assert "KEY3" in output
        assert "Summary:" in output

    def test_conflict_detection_and_display(self):
        """Test detecting and displaying conflicts."""
        local_vars = {"API_KEY": "local_secret", "DB_HOST": "localhost"}
        remote_vars = {"API_KEY": "remote_secret", "DB_HOST": "localhost"}
        
        sync = EnvSyncManager()
        diffs = sync.compare(local_vars, remote_vars)
        
        # Check for conflicts
        assert sync.has_conflicts(diffs)
        conflicts = sync.get_conflicts(diffs)
        assert len(conflicts) == 1
        assert conflicts[0].key == "API_KEY"
        
        # Format conflicts
        formatter = DiffFormatter(use_color=False)
        output = formatter.format_diff(conflicts[0])
        
        assert "API_KEY" in output
        assert "local_secret" in output
        assert "remote_secret" in output

    def test_full_sync_cycle(self):
        """Test complete sync cycle from parse to merge to serialize."""
        # Initial local state
        local_content = "KEY1=value1\nKEY2=value2"
        
        # Remote state with changes
        remote_content = "KEY1=updated\nKEY3=value3"
        
        parser = EnvParser()
        local_vars = parser.parse(local_content)
        remote_vars = parser.parse(remote_content)
        
        # Analyze differences
        sync = EnvSyncManager()
        diffs = sync.compare(local_vars, remote_vars)
        
        # Verify we detected changes
        assert len(diffs) == 3
        assert sync.has_conflicts(diffs)
        
        # Merge with remote strategy
        merged = sync.merge(local_vars, remote_vars, strategy="remote")
        
        # Verify merged result
        assert merged["KEY1"] == "updated"
        assert merged["KEY2"] == "value2"  # Preserved from local
        assert merged["KEY3"] == "value3"  # Added from remote
        
        # Serialize result
        result = parser.serialize(merged)
        assert "KEY1=updated" in result
        assert "KEY2=value2" in result
        assert "KEY3=value3" in result
