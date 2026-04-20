"""Cross-reference checker for .env files.

Detects variables that reference other variables (via ${VAR} or $VAR syntax)
and reports broken references where the referenced variable is not defined.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set

# Matches ${VAR_NAME} and $VAR_NAME patterns
_REF_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class CrossRefEntry:
    """Represents a single cross-reference found in a variable value."""

    source_key: str      # The variable whose value contains the reference
    referenced_key: str  # The variable being referenced
    resolved: bool       # Whether the referenced variable exists

    def __repr__(self) -> str:  # pragma: no cover
        status = "ok" if self.resolved else "broken"
        return f"CrossRefEntry({self.source_key!r} -> {self.referenced_key!r} [{status}])"


@dataclass
class CrossRefResult:
    """Result of a cross-reference analysis."""

    entries: List[CrossRefEntry] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CrossRefResult(total={len(self.entries)}, "
            f"broken={len(self.broken)}, resolved={len(self.resolved)})"
        )

    @property
    def broken(self) -> List[CrossRefEntry]:
        """Return only entries with unresolved references."""
        return [e for e in self.entries if not e.resolved]

    @property
    def resolved(self) -> List[CrossRefEntry]:
        """Return only entries with successfully resolved references."""
        return [e for e in self.entries if e.resolved]

    @property
    def is_clean(self) -> bool:
        """True when there are no broken cross-references."""
        return len(self.broken) == 0

    @property
    def broken_keys(self) -> Set[str]:
        """Set of source keys that contain at least one broken reference."""
        return {e.source_key for e in self.broken}


class EnvCrossRefChecker:
    """Scans a dict of env vars for internal cross-references and validates them."""

    def __init__(self, *, allow_external: bool = False) -> None:
        """
        Args:
            allow_external: When True, references to keys not present in the
                            supplied vars dict are still marked as resolved
                            (useful when vars may be injected from the shell).
        """
        self.allow_external = allow_external

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, vars: Dict[str, str]) -> CrossRefResult:
        """Analyse *vars* and return a :class:`CrossRefResult`.

        Args:
            vars: Mapping of variable name -> value to inspect.

        Returns:
            A :class:`CrossRefResult` describing every reference found.
        """
        defined: Set[str] = set(vars.keys())
        entries: List[CrossRefEntry] = []

        for key, value in vars.items():
            for ref_key in self._extract_refs(value):
                resolved = ref_key in defined or self.allow_external
                entries.append(
                    CrossRefEntry(
                        source_key=key,
                        referenced_key=ref_key,
                        resolved=resolved,
                    )
                )

        return CrossRefResult(entries=entries)

    def graph(self, vars: Dict[str, str]) -> Dict[str, Set[str]]:
        """Return a dependency graph as ``{key: {referenced_keys}}``.

        Only keys that actually contain references are included.
        """
        result: Dict[str, Set[str]] = {}
        for key, value in vars.items():
            refs = self._extract_refs(value)
            if refs:
                result[key] = refs
        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_refs(value: str) -> Set[str]:
        """Return all variable names referenced inside *value*."""
        refs: Set[str] = set()
        for m in _REF_PATTERN.finditer(value):
            # group(1) -> ${NAME}, group(2) -> $NAME
            refs.add(m.group(1) or m.group(2))
        return refs
