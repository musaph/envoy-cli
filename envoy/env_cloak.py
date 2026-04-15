"""env_cloak.py — selectively hide env var values based on key patterns."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

_CLOAK_SYMBOL = "<cloaked>"


@dataclass
class CloakChange:
    key: str
    original: str
    cloaked: str

    def __repr__(self) -> str:
        return f"CloakChange(key={self.key!r}, cloaked={self.cloaked!r})"


@dataclass
class CloakResult:
    vars: Dict[str, str] = field(default_factory=dict)
    changes: List[CloakChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def cloaked_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return f"CloakResult(total={len(self.vars)}, cloaked={len(self.changes)})"


class EnvCloaker:
    """Hide variable values matching key patterns, replacing them with a placeholder."""

    def __init__(
        self,
        patterns: Optional[List[str]] = None,
        symbol: str = _CLOAK_SYMBOL,
    ) -> None:
        self._patterns = [re.compile(p, re.IGNORECASE) for p in (patterns or [])]
        self._symbol = symbol

    def _should_cloak(self, key: str) -> bool:
        return any(p.search(key) for p in self._patterns)

    def cloak(self, vars: Dict[str, str]) -> CloakResult:
        out: Dict[str, str] = {}
        changes: List[CloakChange] = []
        for key, value in vars.items():
            if self._should_cloak(key):
                out[key] = self._symbol
                changes.append(CloakChange(key=key, original=value, cloaked=self._symbol))
            else:
                out[key] = value
        return CloakResult(vars=out, changes=changes)

    def uncloak(self, cloaked: Dict[str, str], original: Dict[str, str]) -> Dict[str, str]:
        """Restore original values for cloaked keys using a reference dict."""
        out = dict(cloaked)
        for key, value in cloaked.items():
            if value == self._symbol and key in original:
                out[key] = original[key]
        return out
