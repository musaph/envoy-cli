"""Scope-based variable filtering: restrict or expose vars by named scope."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class ScopeResult:
    scope: str
    included: Dict[str, str] = field(default_factory=dict)
    excluded_keys: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"ScopeResult(scope={self.scope!r}, "
            f"included={len(self.included)}, "
            f"excluded={len(self.excluded_keys)})"
        )


class EnvScope:
    """Filter environment variables by scope using prefix or explicit allow-lists."""

    def __init__(self, scopes: Optional[Dict[str, List[str]]] = None) -> None:
        """
        Args:
            scopes: mapping of scope name -> list of key prefixes or exact keys.
                    e.g. {"backend": ["DB_", "REDIS_"], "frontend": ["NEXT_PUBLIC_"]}
        """
        self._scopes: Dict[str, List[str]] = scopes or {}

    def register(self, scope: str, patterns: List[str]) -> None:
        """Register or overwrite patterns for a scope."""
        self._scopes[scope] = patterns

    def list_scopes(self) -> List[str]:
        """Return all registered scope names."""
        return list(self._scopes.keys())

    def _matches(self, key: str, patterns: List[str]) -> bool:
        for pattern in patterns:
            if pattern.endswith("_") and key.startswith(pattern):
                return True
            if key == pattern:
                return True
        return False

    def apply(self, vars: Dict[str, str], scope: str) -> ScopeResult:
        """Return only variables that match the given scope's patterns."""
        patterns = self._scopes.get(scope, [])
        included: Dict[str, str] = {}
        excluded: List[str] = []
        for key, value in vars.items():
            if self._matches(key, patterns):
                included[key] = value
            else:
                excluded.append(key)
        return ScopeResult(scope=scope, included=included, excluded_keys=excluded)

    def keys_for_scope(self, vars: Dict[str, str], scope: str) -> Set[str]:
        """Return the set of keys that belong to the given scope."""
        return set(self.apply(vars, scope).included.keys())

    def unscoped(self, vars: Dict[str, str]) -> Dict[str, str]:
        """Return variables that do not belong to any registered scope."""
        all_scoped: Set[str] = set()
        for scope in self._scopes:
            all_scoped |= self.keys_for_scope(vars, scope)
        return {k: v for k, v in vars.items() if k not in all_scoped}
