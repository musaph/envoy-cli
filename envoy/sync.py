"""Sync manager for comparing and merging .env files."""

from typing import Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class SyncAction(Enum):
    """Possible sync actions for a key."""
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    CONFLICT = "conflict"
    NO_CHANGE = "no_change"


@dataclass
class SyncDiff:
    """Represents a difference between local and remote env variables."""
    key: str
    action: SyncAction
    local_value: Optional[str]
    remote_value: Optional[str]


class EnvSyncManager:
    """Manages synchronization between local and remote .env files."""

    def __init__(self):
        pass

    def compare(self, local_vars: Dict[str, str], remote_vars: Dict[str, str]) -> list[SyncDiff]:
        """Compare local and remote variables and return differences.
        
        Args:
            local_vars: Dictionary of local environment variables
            remote_vars: Dictionary of remote environment variables
            
        Returns:
            List of SyncDiff objects representing differences
        """
        diffs = []
        all_keys = set(local_vars.keys()) | set(remote_vars.keys())
        
        for key in sorted(all_keys):
            local_val = local_vars.get(key)
            remote_val = remote_vars.get(key)
            
            if local_val is None and remote_val is not None:
                # Key exists only remotely
                diffs.append(SyncDiff(key, SyncAction.ADD, None, remote_val))
            elif local_val is not None and remote_val is None:
                # Key exists only locally
                diffs.append(SyncDiff(key, SyncAction.DELETE, local_val, None))
            elif local_val != remote_val:
                # Key exists in both but values differ
                diffs.append(SyncDiff(key, SyncAction.CONFLICT, local_val, remote_val))
            else:
                # Values match
                diffs.append(SyncDiff(key, SyncAction.NO_CHANGE, local_val, remote_val))
        
        return diffs

    def merge(self, local_vars: Dict[str, str], remote_vars: Dict[str, str], 
              strategy: str = "remote") -> Dict[str, str]:
        """Merge local and remote variables using specified strategy.
        
        Args:
            local_vars: Dictionary of local environment variables
            remote_vars: Dictionary of remote environment variables
            strategy: Merge strategy - "remote", "local", or "newest"
            
        Returns:
            Merged dictionary of environment variables
        """
        if strategy == "remote":
            # Remote takes precedence
            return {**local_vars, **remote_vars}
        elif strategy == "local":
            # Local takes precedence
            return {**remote_vars, **local_vars}
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

    def has_conflicts(self, diffs: list[SyncDiff]) -> bool:
        """Check if there are any conflicts in the diff list."""
        return any(diff.action == SyncAction.CONFLICT for diff in diffs)

    def get_conflicts(self, diffs: list[SyncDiff]) -> list[SyncDiff]:
        """Get only the conflicting diffs."""
        return [diff for diff in diffs if diff.action == SyncAction.CONFLICT]
