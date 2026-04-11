"""Detect and report unset or placeholder values in .env files."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

PLACEHOLDER_PATTERNS = [
    re.compile(r'^<.+>$'),          # <YOUR_VALUE>
    re.compile(r'^\{\{.+\}\}$'),   # {{placeholder}}
    re.compile(r'^CHANGE_ME$', re.IGNORECASE),
    re.compile(r'^TODO$', re.IGNORECASE),
    re.compile(r'^REPLACE_ME$', re.IGNORECASE),
    re.compile(r'^YOUR_.+$', re.IGNORECASE),
    re.compile(r'^.*PLACEHOLDER.*$', re.IGNORECASE),
]


@dataclass
class PlaceholderMatch:
    key: str
    value: str
    reason: str

    def __repr__(self) -> str:
        return f"PlaceholderMatch(key={self.key!r}, reason={self.reason!r})"


@dataclass
class PlaceholderResult:
    matches: List[PlaceholderMatch] = field(default_factory=list)
    checked: int = 0

    @property
    def found(self) -> bool:
        return len(self.matches) > 0

    def __repr__(self) -> str:
        return f"PlaceholderResult(found={self.found}, count={len(self.matches)}/{self.checked})"


class EnvPlaceholderDetector:
    """Scans env var dicts for unset or placeholder values."""

    def __init__(self, extra_patterns: Optional[List[re.Pattern]] = None) -> None:
        self._patterns = list(PLACEHOLDER_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)

    def is_placeholder(self, value: str) -> Optional[str]:
        """Return a reason string if the value looks like a placeholder, else None."""
        if value == "":
            return "empty value"
        for pat in self._patterns:
            if pat.match(value):
                return f"matches pattern {pat.pattern!r}"
        return None

    def detect(self, vars: Dict[str, str]) -> PlaceholderResult:
        """Scan all vars and return a PlaceholderResult."""
        result = PlaceholderResult(checked=len(vars))
        for key, value in vars.items():
            reason = self.is_placeholder(value)
            if reason:
                result.matches.append(PlaceholderMatch(key=key, value=value, reason=reason))
        return result
