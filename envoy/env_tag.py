"""Tag management for .env variables — attach metadata labels to keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class TagResult:
    tagged: Dict[str, List[str]] = field(default_factory=dict)   # key -> [tags]
    untagged: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"TagResult(tagged={len(self.tagged)}, "
            f"untagged={len(self.untagged)}, warnings={len(self.warnings)})"
        )


class EnvTagger:
    """Attach and query string tags on environment variable keys."""

    def __init__(self, rules: Optional[Dict[str, List[str]]] = None) -> None:
        # rules: {tag_name: [key_prefix_or_exact, ...]}
        self._rules: Dict[str, List[str]] = rules or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tag(self, vars: Dict[str, str]) -> TagResult:
        """Apply all rules and return a TagResult for *vars*."""
        tagged: Dict[str, List[str]] = {}
        untagged: List[str] = []
        warnings: List[str] = []

        for key in vars:
            key_tags = self._tags_for_key(key)
            if key_tags:
                tagged[key] = sorted(key_tags)
            else:
                untagged.append(key)

        return TagResult(tagged=tagged, untagged=untagged, warnings=warnings)

    def keys_with_tag(self, vars: Dict[str, str], tag: str) -> List[str]:
        """Return all keys in *vars* that match *tag*."""
        if tag not in self._rules:
            return []
        patterns = self._rules[tag]
        return [
            k for k in vars
            if any(k == p or k.startswith(p) for p in patterns)
        ]

    def all_tags(self) -> Set[str]:
        """Return the set of configured tag names."""
        return set(self._rules.keys())

    def add_rule(self, tag: str, pattern: str) -> None:
        """Register *pattern* under *tag* (prefix or exact match)."""
        self._rules.setdefault(tag, []).append(pattern)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tags_for_key(self, key: str) -> Set[str]:
        matched: Set[str] = set()
        for tag, patterns in self._rules.items():
            for p in patterns:
                if key == p or key.startswith(p):
                    matched.add(tag)
                    break
        return matched
