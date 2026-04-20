"""Spotlight: highlight and surface env vars matching a priority pattern list."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class SpotlightMatch:
    key: str
    value: str
    pattern: str
    priority: int

    def __repr__(self) -> str:
        return f"SpotlightMatch(key={self.key!r}, pattern={self.pattern!r}, priority={self.priority})"


@dataclass
class SpotlightResult:
    matches: List[SpotlightMatch] = field(default_factory=list)
    unmatched_keys: List[str] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return len(self.matches) > 0

    @property
    def top_priority(self) -> Optional[SpotlightMatch]:
        if not self.matches:
            return None
        return min(self.matches, key=lambda m: m.priority)

    @property
    def matched_keys(self) -> List[str]:
        return [m.key for m in self.matches]

    def __repr__(self) -> str:
        return (
            f"SpotlightResult(matches={len(self.matches)}, "
            f"unmatched={len(self.unmatched_keys)})"
        )


class EnvSpotlight:
    """Surface env vars by matching against a prioritised list of regex patterns."""

    def __init__(self, patterns: List[str], case_sensitive: bool = False) -> None:
        self._raw = patterns
        flags = 0 if case_sensitive else re.IGNORECASE
        self._compiled = [
            (i + 1, p, re.compile(p, flags)) for i, p in enumerate(patterns)
        ]

    def scan(self, vars: Dict[str, str]) -> SpotlightResult:
        matches: List[SpotlightMatch] = []
        matched_keys: set = set()

        for key, value in vars.items():
            for priority, raw_pattern, compiled in self._compiled:
                if compiled.search(key):
                    matches.append(
                        SpotlightMatch(
                            key=key,
                            value=value,
                            pattern=raw_pattern,
                            priority=priority,
                        )
                    )
                    matched_keys.add(key)
                    break

        unmatched = [k for k in vars if k not in matched_keys]
        matches.sort(key=lambda m: (m.priority, m.key))
        return SpotlightResult(matches=matches, unmatched_keys=unmatched)
