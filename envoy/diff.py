"""Diff formatter for displaying sync differences."""

from typing import List
from envoy.sync import SyncDiff, SyncAction


class DiffFormatter:
    """Formats sync differences for display."""

    # ANSI color codes
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, use_color: bool = True):
        """Initialize formatter.
        
        Args:
            use_color: Whether to use ANSI color codes in output
        """
        self.use_color = use_color

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.use_color:
            return text
        return f"{color}{text}{self.RESET}"

    def format_diff(self, diff: SyncDiff) -> str:
        """Format a single diff for display.
        
        Args:
            diff: SyncDiff object to format
            
        Returns:
            Formatted string representation
        """
        if diff.action == SyncAction.NO_CHANGE:
            return f"  {diff.key} = {diff.local_value}"
        
        elif diff.action == SyncAction.ADD:
            symbol = self._colorize("+", self.GREEN)
            value = self._colorize(diff.remote_value, self.GREEN)
            return f"{symbol} {diff.key} = {value}"
        
        elif diff.action == SyncAction.DELETE:
            symbol = self._colorize("-", self.RED)
            value = self._colorize(diff.local_value, self.RED)
            return f"{symbol} {diff.key} = {value}"
        
        elif diff.action == SyncAction.CONFLICT:
            symbol = self._colorize("!", self.YELLOW)
            local_val = self._colorize(diff.local_value, self.RED)
            remote_val = self._colorize(diff.remote_value, self.GREEN)
            return f"{symbol} {diff.key}\n  Local:  {local_val}\n  Remote: {remote_val}"
        
        return f"  {diff.key}"

    def format_summary(self, diffs: List[SyncDiff]) -> str:
        """Format a summary of all diffs.
        
        Args:
            diffs: List of SyncDiff objects
            
        Returns:
            Formatted summary string
        """
        adds = sum(1 for d in diffs if d.action == SyncAction.ADD)
        deletes = sum(1 for d in diffs if d.action == SyncAction.DELETE)
        conflicts = sum(1 for d in diffs if d.action == SyncAction.CONFLICT)
        unchanged = sum(1 for d in diffs if d.action == SyncAction.NO_CHANGE)
        
        parts = []
        if adds > 0:
            parts.append(self._colorize(f"{adds} to add", self.GREEN))
        if deletes > 0:
            parts.append(self._colorize(f"{deletes} to delete", self.RED))
        if conflicts > 0:
            parts.append(self._colorize(f"{conflicts} conflicts", self.YELLOW))
        if unchanged > 0:
            parts.append(f"{unchanged} unchanged")
        
        summary = ", ".join(parts) if parts else "No changes"
        title = self._colorize("Summary:", self.BOLD)
        return f"{title} {summary}"

    def format_all(self, diffs: List[SyncDiff], show_unchanged: bool = False) -> str:
        """Format all diffs with summary.
        
        Args:
            diffs: List of SyncDiff objects
            show_unchanged: Whether to show unchanged variables
            
        Returns:
            Complete formatted output
        """
        lines = []
        
        for diff in diffs:
            if not show_unchanged and diff.action == SyncAction.NO_CHANGE:
                continue
            lines.append(self.format_diff(diff))
        
        if lines:
            lines.append("")  # Empty line before summary
        lines.append(self.format_summary(diffs))
        
        return "\n".join(lines)
