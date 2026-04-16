from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class HighlightMatch:
    key: str
    value: str
    pattern: str

    def __repr__(self) -> str:
        return f"HighlightMatch(key={self.key!r}, pattern={self.pattern!r})"


@dataclass
class HighlightResult:
    matches: List[HighlightMatch] = field(default_factory=list)
    unmatched_keys: List[str] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return len(self.matches) > 0

    @property
    def matched_keys(self) -> List[str]:
        return [m.key for m in self.matches]

    def __repr__(self) -> str:
        return (
            f"HighlightResult(matches={len(self.matches)}, "
            f"unmatched={len(self.unmatched_keys)})"
        )


class EnvHighlighter:
    def __init__(self, patterns: List[str], case_sensitive: bool = False):
        self.patterns = patterns
        self.flags = 0 if case_sensitive else re.IGNORECASE
        self._compiled = [re.compile(p, self.flags) for p in patterns]

    def highlight(self, vars: Dict[str, str]) -> HighlightResult:
        matches: List[HighlightMatch] = []
        unmatched: List[str] = []

        for key, value in vars.items():
            matched = False
            for pattern, compiled in zip(self.patterns, self._compiled):
                if compiled.search(key) or compiled.search(value):
                    matches.append(HighlightMatch(key=key, value=value, pattern=pattern))
                    matched = True
                    break
            if not matched:
                unmatched.append(key)

        return HighlightResult(matches=matches, unmatched_keys=unmatched)

    def highlight_keys_only(self, vars: Dict[str, str]) -> HighlightResult:
        matches: List[HighlightMatch] = []
        unmatched: List[str] = []

        for key, value in vars.items():
            matched = False
            for pattern, compiled in zip(self.patterns, self._compiled):
                if compiled.search(key):
                    matches.append(HighlightMatch(key=key, value=value, pattern=pattern))
                    matched = True
                    break
            if not matched:
                unmatched.append(key)

        return HighlightResult(matches=matches, unmatched_keys=unmatched)
