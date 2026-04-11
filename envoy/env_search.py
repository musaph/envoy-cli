from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class SearchMatch:
    key: str
    value: str
    match_on: str  # 'key', 'value', or 'both'

    def __repr__(self) -> str:
        return f"SearchMatch(key={self.key!r}, match_on={self.match_on!r})"


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)
    query: str = ""

    def __repr__(self) -> str:
        return f"SearchResult(query={self.query!r}, matches={len(self.matches)})"

    @property
    def found(self) -> bool:
        return len(self.matches) > 0

    @property
    def keys(self) -> List[str]:
        return [m.key for m in self.matches]


class EnvSearch:
    def __init__(self, case_sensitive: bool = False, search_values: bool = True):
        self.case_sensitive = case_sensitive
        self.search_values = search_values

    def search(self, vars: Dict[str, str], query: str) -> SearchResult:
        """Search env vars by key and optionally value using substring or regex."""
        matches: List[SearchMatch] = []
        flags = 0 if self.case_sensitive else re.IGNORECASE

        try:
            pattern = re.compile(query, flags)
        except re.error:
            pattern = re.compile(re.escape(query), flags)

        for key, value in vars.items():
            key_hit = bool(pattern.search(key))
            val_hit = self.search_values and bool(pattern.search(value))

            if key_hit and val_hit:
                matches.append(SearchMatch(key=key, value=value, match_on="both"))
            elif key_hit:
                matches.append(SearchMatch(key=key, value=value, match_on="key"))
            elif val_hit:
                matches.append(SearchMatch(key=key, value=value, match_on="value"))

        return SearchResult(matches=matches, query=query)

    def filter_by_prefix(self, vars: Dict[str, str], prefix: str) -> Dict[str, str]:
        """Return only vars whose keys start with the given prefix."""
        cmp_prefix = prefix if self.case_sensitive else prefix.upper()
        return {
            k: v for k, v in vars.items()
            if (k if self.case_sensitive else k.upper()).startswith(cmp_prefix)
        }
