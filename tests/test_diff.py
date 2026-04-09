"""Tests for the diff formatter."""

import pytest
from envoy.diff import DiffFormatter
from envoy.sync import SyncDiff, SyncAction


class TestDiffFormatter:
    """Test cases for DiffFormatter."""

    def test_format_no_change(self):
        """Test formatting unchanged variable."""
        formatter = DiffFormatter(use_color=False)
        diff = SyncDiff("KEY1", SyncAction.NO_CHANGE, "value", "value")
        
        result = formatter.format_diff(diff)
        
        assert result == "  KEY1 = value"

    def test_format_add(self):
        """Test formatting added variable."""
        formatter = DiffFormatter(use_color=False)
        diff = SyncDiff("KEY1", SyncAction.ADD, None, "new_value")
        
        result = formatter.format_diff(diff)
        
        assert result == "+ KEY1 = new_value"

    def test_format_delete(self):
        """Test formatting deleted variable."""
        formatter = DiffFormatter(use_color=False)
        diff = SyncDiff("KEY1", SyncAction.DELETE, "old_value", None)
        
        result = formatter.format_diff(diff)
        
        assert result == "- KEY1 = old_value"

    def test_format_conflict(self):
        """Test formatting conflicting variable."""
        formatter = DiffFormatter(use_color=False)
        diff = SyncDiff("KEY1", SyncAction.CONFLICT, "local_val", "remote_val")
        
        result = formatter.format_diff(diff)
        
        assert "! KEY1" in result
        assert "Local:  local_val" in result
        assert "Remote: remote_val" in result

    def test_format_with_colors(self):
        """Test that colors are applied when enabled."""
        formatter = DiffFormatter(use_color=True)
        diff = SyncDiff("KEY1", SyncAction.ADD, None, "value")
        
        result = formatter.format_diff(diff)
        
        # Should contain ANSI color codes
        assert "\033[" in result
        assert "KEY1" in result

    def test_format_without_colors(self):
        """Test that colors are not applied when disabled."""
        formatter = DiffFormatter(use_color=False)
        diff = SyncDiff("KEY1", SyncAction.ADD, None, "value")
        
        result = formatter.format_diff(diff)
        
        # Should not contain ANSI color codes
        assert "\033[" not in result

    def test_format_summary_empty(self):
        """Test summary with no diffs."""
        formatter = DiffFormatter(use_color=False)
        diffs = []
        
        result = formatter.format_summary(diffs)
        
        assert "Summary:" in result
        assert "No changes" in result

    def test_format_summary_mixed(self):
        """Test summary with multiple diff types."""
        formatter = DiffFormatter(use_color=False)
        diffs = [
            SyncDiff("K1", SyncAction.ADD, None, "v1"),
            SyncDiff("K2", SyncAction.ADD, None, "v2"),
            SyncDiff("K3", SyncAction.DELETE, "v3", None),
            SyncDiff("K4", SyncAction.CONFLICT, "local", "remote"),
            SyncDiff("K5", SyncAction.NO_CHANGE, "v5", "v5"),
        ]
        
        result = formatter.format_summary(diffs)
        
        assert "2 to add" in result
        assert "1 to delete" in result
        assert "1 conflicts" in result
        assert "1 unchanged" in result

    def test_format_all_without_unchanged(self):
        """Test formatting all diffs without unchanged items."""
        formatter = DiffFormatter(use_color=False)
        diffs = [
            SyncDiff("K1", SyncAction.ADD, None, "v1"),
            SyncDiff("K2", SyncAction.NO_CHANGE, "v2", "v2"),
            SyncDiff("K3", SyncAction.DELETE, "v3", None),
        ]
        
        result = formatter.format_all(diffs, show_unchanged=False)
        
        assert "+ K1" in result
        assert "- K3" in result
        assert "K2" not in result.split("Summary:")[0]  # K2 not in main output
        assert "Summary:" in result

    def test_format_all_with_unchanged(self):
        """Test formatting all diffs including unchanged items."""
        formatter = DiffFormatter(use_color=False)
        diffs = [
            SyncDiff("K1", SyncAction.ADD, None, "v1"),
            SyncDiff("K2", SyncAction.NO_CHANGE, "v2", "v2"),
        ]
        
        result = formatter.format_all(diffs, show_unchanged=True)
        
        assert "+ K1" in result
        assert "K2 = v2" in result
        assert "Summary:" in result

    def test_format_all_only_unchanged(self):
        """Test formatting when all diffs are unchanged."""
        formatter = DiffFormatter(use_color=False)
        diffs = [
            SyncDiff("K1", SyncAction.NO_CHANGE, "v1", "v1"),
            SyncDiff("K2", SyncAction.NO_CHANGE, "v2", "v2"),
        ]
        
        result = formatter.format_all(diffs, show_unchanged=False)
        
        # Should only show summary when all unchanged
        assert "Summary:" in result
        assert "2 unchanged" in result
