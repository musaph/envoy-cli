"""Split a flat .env variable set into multiple grouped output files by prefix."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SplitResult:
    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    unmatched: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SplitResult(groups={list(self.groups.keys())}, "
            f"unmatched={len(self.unmatched)}, errors={len(self.errors)})"
        )

    @property
    def has_unmatched(self) -> bool:
        return bool(self.unmatched)

    @property
    def group_names(self) -> List[str]:
        return list(self.groups.keys())


class EnvSplitter:
    """Split env vars into named groups based on key prefixes."""

    def __init__(self, strip_prefix: bool = True) -> None:
        self._strip_prefix = strip_prefix

    def split(
        self,
        vars: Dict[str, str],
        prefixes: List[str],
        default_group: Optional[str] = None,
    ) -> SplitResult:
        """Partition *vars* into groups keyed by matching prefix.

        Parameters
        ----------
        vars:
            Flat mapping of env variable names to values.
        prefixes:
            Ordered list of prefix strings to match against.  First match wins.
        default_group:
            If provided, unmatched keys are placed into this group instead of
            the ``unmatched`` bucket.
        """
        result = SplitResult()

        for key, value in vars.items():
            matched = False
            for prefix in prefixes:
                if key.startswith(prefix):
                    group_key = key[len(prefix):] if self._strip_prefix else key
                    result.groups.setdefault(prefix, {})[group_key] = value
                    matched = True
                    break

            if not matched:
                if default_group is not None:
                    result.groups.setdefault(default_group, {})[key] = value
                else:
                    result.unmatched[key] = value

        return result

    def merge(self, split_result: SplitResult) -> Dict[str, str]:
        """Reconstruct a flat dict from a SplitResult (inverse of split)."""
        merged: Dict[str, str] = {}
        for group, vars in split_result.groups.items():
            for k, v in vars.items():
                merged[k] = v
        merged.update(split_result.unmatched)
        return merged
