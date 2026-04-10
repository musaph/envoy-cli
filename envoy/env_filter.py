"""Filter environment variables by key patterns, prefixes, or value conditions."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FilterResult:
    matched: Dict[str, str]
    excluded: Dict[str, str]
    total: int

    def __repr__(self) -> str:
        return (
            f"FilterResult(matched={len(self.matched)}, "
            f"excluded={len(self.excluded)}, total={self.total})"
        )


class EnvFilter:
    """Filter env vars using prefix, glob pattern, or regex rules."""

    def __init__(
        self,
        prefixes: Optional[List[str]] = None,
        patterns: Optional[List[str]] = None,
        regex: Optional[str] = None,
        exclude_prefixes: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> None:
        self._prefixes = [p.upper() for p in (prefixes or [])]
        self._patterns = patterns or []
        self._regex = re.compile(regex) if regex else None
        self._exclude_prefixes = [p.upper() for p in (exclude_prefixes or [])]
        self._exclude_patterns = exclude_patterns or []

    def _is_included(self, key: str) -> bool:
        """Return True if key passes all inclusion rules (or no rules set)."""
        has_rule = bool(self._prefixes or self._patterns or self._regex)
        if not has_rule:
            return True
        if self._prefixes and any(key.upper().startswith(p) for p in self._prefixes):
            return True
        if self._patterns and any(fnmatch.fnmatch(key, pat) for pat in self._patterns):
            return True
        if self._regex and self._regex.search(key):
            return True
        return False

    def _is_excluded(self, key: str) -> bool:
        """Return True if key matches any exclusion rule."""
        if self._exclude_prefixes and any(
            key.upper().startswith(p) for p in self._exclude_prefixes
        ):
            return True
        if self._exclude_patterns and any(
            fnmatch.fnmatch(key, pat) for pat in self._exclude_patterns
        ):
            return True
        return False

    def apply(self, vars: Dict[str, str]) -> FilterResult:
        """Apply filter rules and return a FilterResult."""
        matched: Dict[str, str] = {}
        excluded: Dict[str, str] = {}
        for key, value in vars.items():
            if self._is_excluded(key):
                excluded[key] = value
            elif self._is_included(key):
                matched[key] = value
            else:
                excluded[key] = value
        return FilterResult(matched=matched, excluded=excluded, total=len(vars))
