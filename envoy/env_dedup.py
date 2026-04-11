"""Deduplication of .env variables — detects and removes duplicate keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DedupResult:
    original: Dict[str, str]
    deduplicated: Dict[str, str]
    duplicates: Dict[str, List[str]]  # key -> list of all values seen

    def __repr__(self) -> str:
        return (
            f"DedupResult(total={len(self.original)}, "
            f"unique={len(self.deduplicated)}, "
            f"duplicate_keys={len(self.duplicates)})"
        )

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)

    @property
    def removed_count(self) -> int:
        return len(self.original) - len(self.deduplicated)


class EnvDeduplicator:
    """Detects and resolves duplicate keys in a list of (key, value) pairs."""

    def __init__(self, strategy: str = "last") -> None:
        """
        :param strategy: 'first' keeps the first occurrence,
                         'last'  keeps the last occurrence (default).
        """
        if strategy not in ("first", "last"):
            raise ValueError("strategy must be 'first' or 'last'")
        self.strategy = strategy

    def deduplicate(self, pairs: List[Tuple[str, str]]) -> DedupResult:
        """Process a list of (key, value) pairs and return a DedupResult."""
        seen: Dict[str, List[str]] = {}
        for key, value in pairs:
            seen.setdefault(key, []).append(value)

        duplicates = {k: v for k, v in seen.items() if len(v) > 1}

        if self.strategy == "first":
            deduped: Dict[str, str] = {}
            for key, value in pairs:
                if key not in deduped:
                    deduped[key] = value
        else:  # last
            deduped = {}
            for key, value in pairs:
                deduped[key] = value

        original = {k: vals[-1] for k, vals in seen.items()}

        return DedupResult(
            original=original,
            deduplicated=deduped,
            duplicates=duplicates,
        )

    def from_dict(self, vars_: Dict[str, str]) -> DedupResult:
        """Convenience wrapper when the caller already has a plain dict (no duplicates)."""
        pairs = list(vars_.items())
        return self.deduplicate(pairs)
