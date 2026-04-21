"""Tokenize env var values into constituent parts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class TokenizeChange:
    key: str
    original: str
    tokens: List[str]

    def __repr__(self) -> str:
        return f"TokenizeChange(key={self.key!r}, tokens={self.tokens!r})"


@dataclass
class TokenizeResult:
    changes: List[TokenizeChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"TokenizeResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvTokenizer:
    """Split env var values into tokens using a configurable delimiter pattern."""

    DEFAULT_PATTERN = r"[\s,;:|]+"

    def __init__(
        self,
        pattern: Optional[str] = None,
        keys: Optional[List[str]] = None,
        min_tokens: int = 2,
    ) -> None:
        self._pattern = re.compile(pattern or self.DEFAULT_PATTERN)
        self._keys = set(keys) if keys else None
        self._min_tokens = min_tokens

    def tokenize(self, vars: Dict[str, str]) -> TokenizeResult:
        """Return a TokenizeResult with per-key token lists."""
        changes: List[TokenizeChange] = []
        skipped: List[str] = []

        for key, value in vars.items():
            if self._keys is not None and key not in self._keys:
                continue
            tokens = [t for t in self._pattern.split(value) if t]
            if len(tokens) >= self._min_tokens:
                changes.append(TokenizeChange(key=key, original=value, tokens=tokens))
            else:
                skipped.append(key)

        return TokenizeResult(changes=changes, skipped=skipped)

    def as_dict(self, result: TokenizeResult) -> Dict[str, List[str]]:
        """Return a mapping of key -> token list from a TokenizeResult."""
        return {c.key: c.tokens for c in result.changes}
