"""Normalize .env variable values: strip excess whitespace, fix line endings, and standardize quoting."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class NormalizeChange:
    key: str
    original: str
    normalized: str
    reason: str

    def __repr__(self) -> str:
        return f"NormalizeChange(key={self.key!r}, reason={self.reason!r})"


@dataclass
class NormalizeResult:
    changes: List[NormalizeChange] = field(default_factory=list)
    vars: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return f"NormalizeResult(changes={len(self.changes)}, has_changes={self.has_changes})"


class EnvNormalizer:
    """Normalize environment variable values."""

    def __init__(self, strip_quotes: bool = True, fix_line_endings: bool = True):
        self.strip_quotes = strip_quotes
        self.fix_line_endings = fix_line_endings

    def normalize(self, vars: Dict[str, str]) -> NormalizeResult:
        result_vars: Dict[str, str] = {}
        changes: List[NormalizeChange] = []

        for key, value in vars.items():
            normalized, reason = self._normalize_value(value)
            result_vars[key] = normalized
            if normalized != value:
                changes.append(NormalizeChange(
                    key=key,
                    original=value,
                    normalized=normalized,
                    reason=reason or "normalized",
                ))

        return NormalizeResult(changes=changes, vars=result_vars)

    def _normalize_value(self, value: str) -> tuple:
        original = value
        reasons = []

        if self.fix_line_endings and "\r\n" in value:
            value = value.replace("\r\n", "\n")
            reasons.append("fixed line endings")

        stripped = value.strip()
        if stripped != value:
            value = stripped
            reasons.append("stripped whitespace")

        if self.strip_quotes:
            unquoted, changed = self._strip_outer_quotes(value)
            if changed:
                value = unquoted
                reasons.append("removed outer quotes")

        return value, ", ".join(reasons) if reasons else None

    def _strip_outer_quotes(self, value: str):
        if len(value) >= 2:
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                return value[1:-1], True
        return value, False
