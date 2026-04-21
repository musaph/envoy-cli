from dataclasses import dataclass, field
from typing import Dict, List
import re


@dataclass
class UnescapeChange:
    key: str
    original: str
    unescaped: str

    def __repr__(self) -> str:
        return f"UnescapeChange(key={self.key!r}, original={self.original!r}, unescaped={self.unescaped!r})"


@dataclass
class UnescapeResult:
    vars: Dict[str, str]
    changes: List[UnescapeChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return f"UnescapeResult(changed={len(self.changes)}, total={len(self.vars)})"


class EnvUnescaper:
    """Unescape common escape sequences in .env variable values."""

    ESCAPE_MAP = {
        r"\n": "\n",
        r"\t": "\t",
        r"\r": "\r",
        r"\\\\": "\\",
        r"\'": "'",
        r"\\\"": '"',
    }

    def __init__(self, keys: List[str] = None):
        """If keys is provided, only unescape those keys; otherwise unescape all."""
        self._keys = set(keys) if keys else None

    def _unescape(self, value: str) -> str:
        result = value
        for escaped, replacement in self.ESCAPE_MAP.items():
            result = result.replace(escaped, replacement)
        return result

    def unescape(self, vars: Dict[str, str]) -> UnescapeResult:
        out: Dict[str, str] = {}
        changes: List[UnescapeChange] = []

        for key, value in vars.items():
            if self._keys is not None and key not in self._keys:
                out[key] = value
                continue

            unescaped = self._unescape(value)
            out[key] = unescaped
            if unescaped != value:
                changes.append(UnescapeChange(key=key, original=value, unescaped=unescaped))

        return UnescapeResult(vars=out, changes=changes)
