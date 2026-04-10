"""Merge strategies for combining local and remote .env variable sets."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class MergeStrategy(str, Enum):
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    INTERACTIVE = "interactive"  # caller must resolve conflicts externally


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: Dict[str, tuple] = field(default_factory=dict)  # key -> (local, remote)
    added_from_remote: list = field(default_factory=list)
    added_from_local: list = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def __repr__(self) -> str:
        return (
            f"MergeResult(merged={len(self.merged)}, "
            f"conflicts={len(self.conflicts)}, "
            f"added_from_remote={len(self.added_from_remote)}, "
            f"added_from_local={len(self.added_from_local)})"
        )


class EnvMerger:
    """Merges two dictionaries of env variables using a configurable strategy."""

    def __init__(self, strategy: MergeStrategy = MergeStrategy.LOCAL_WINS):
        self.strategy = strategy

    def merge(
        self,
        local: Dict[str, str],
        remote: Dict[str, str],
        overrides: Optional[Dict[str, str]] = None,
    ) -> MergeResult:
        """Merge local and remote env dicts. overrides always win."""
        result = MergeResult()
        all_keys = set(local) | set(remote)
        overrides = overrides or {}

        for key in all_keys:
            if key in overrides:
                result.merged[key] = overrides[key]
                continue

            in_local = key in local
            in_remote = key in remote

            if in_local and not in_remote:
                result.merged[key] = local[key]
                result.added_from_local.append(key)
            elif in_remote and not in_local:
                result.merged[key] = remote[key]
                result.added_from_remote.append(key)
            else:
                # present in both
                if local[key] == remote[key]:
                    result.merged[key] = local[key]
                else:
                    result.conflicts[key] = (local[key], remote[key])
                    if self.strategy == MergeStrategy.LOCAL_WINS:
                        result.merged[key] = local[key]
                    elif self.strategy == MergeStrategy.REMOTE_WINS:
                        result.merged[key] = remote[key]
                    # INTERACTIVE: leave out of merged, caller resolves

        return result
