"""Resolve environment variables by expanding references and applying defaults."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

_REF_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)")


@dataclass
class ResolveResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    unresolved: List[str] = field(default_factory=list)
    expanded: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"ResolveResult(resolved={len(self.resolved)}, "
            f"unresolved={self.unresolved}, expanded={self.expanded})"
        )

    @property
    def is_clean(self) -> bool:
        return len(self.unresolved) == 0


class EnvResolver:
    """Expand $VAR / ${VAR} references within .env variable values."""

    def __init__(self, external: Optional[Dict[str, str]] = None, max_passes: int = 10):
        self._external = external or {}
        self._max_passes = max_passes

    def resolve(self, vars: Dict[str, str]) -> ResolveResult:
        """Return a ResolveResult with all resolvable references expanded."""
        working = dict(vars)
        expanded_keys: set = set()

        for _ in range(self._max_passes):
            changed = False
            for key, value in list(working.items()):
                new_value, did_change = self._expand(value, working)
                if did_change:
                    working[key] = new_value
                    expanded_keys.add(key)
                    changed = True
            if not changed:
                break

        unresolved = [
            key
            for key, value in working.items()
            if _REF_RE.search(value)
        ]

        return ResolveResult(
            resolved=working,
            unresolved=unresolved,
            expanded=sorted(expanded_keys),
        )

    def _expand(self, value: str, context: Dict[str, str]) -> tuple[str, bool]:
        """Expand one pass of variable references; return (new_value, changed)."""
        combined = {**self._external, **context}
        result = []
        last = 0
        changed = False
        for m in _REF_RE.finditer(value):
            ref_name = m.group(1) or m.group(2)
            if ref_name in combined:
                result.append(value[last:m.start()])
                result.append(combined[ref_name])
                last = m.end()
                changed = True
        result.append(value[last:])
        return "".join(result), changed
