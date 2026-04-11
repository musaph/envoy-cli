"""Variable interpolation for .env files.

Supports ${VAR} and $VAR syntax, resolving references within the same
environment dict or from an optional override context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_PATTERN = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationResult:
    resolved: Dict[str, str]
    unresolved_keys: List[str] = field(default_factory=list)
    cycles: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.unresolved_keys and not self.cycles

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"InterpolationResult(resolved={len(self.resolved)}, "
            f"unresolved={self.unresolved_keys}, cycles={self.cycles})"
        )


class EnvInterpolator:
    """Resolve variable references inside env var values."""

    def __init__(self, max_depth: int = 10) -> None:
        self.max_depth = max_depth

    def interpolate(
        self,
        vars: Dict[str, str],
        context: Optional[Dict[str, str]] = None,
    ) -> InterpolationResult:
        """Return a new dict with all resolvable references expanded."""
        base = dict(context or {})
        base.update(vars)  # vars take precedence over context

        resolved: Dict[str, str] = {}
        unresolved: List[str] = []
        cycles: List[str] = []

        for key, value in vars.items():
            try:
                resolved[key] = self._resolve(
                    value, base, visiting=set(), depth=0
                )
            except _CycleError as exc:
                cycles.append(key)
                resolved[key] = value  # keep original
            except _UnresolvedError:
                unresolved.append(key)
                resolved[key] = value  # keep original

        return InterpolationResult(
            resolved=resolved,
            unresolved_keys=unresolved,
            cycles=cycles,
        )

    def _resolve(
        self,
        value: str,
        base: Dict[str, str],
        visiting: set,
        depth: int,
    ) -> str:
        if depth > self.max_depth:
            raise _CycleError("max depth exceeded")

        def replacer(match: re.Match) -> str:
            ref = match.group(1) or match.group(2)
            if ref in visiting:
                raise _CycleError(ref)
            if ref not in base:
                raise _UnresolvedError(ref)
            return self._resolve(
                base[ref], base, visiting | {ref}, depth + 1
            )

        return _PATTERN.sub(replacer, value)


class _CycleError(Exception):
    pass


class _UnresolvedError(Exception):
    pass
