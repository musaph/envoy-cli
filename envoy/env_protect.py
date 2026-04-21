"""env_protect.py — Mark variables as protected to prevent accidental deletion or overwrite."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class ProtectViolation:
    key: str
    reason: str

    def __repr__(self) -> str:
        return f"ProtectViolation(key={self.key!r}, reason={self.reason!r})"


@dataclass
class ProtectResult:
    protected_keys: Set[str] = field(default_factory=set)
    violations: List[ProtectViolation] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.violations) == 0

    @property
    def violation_keys(self) -> List[str]:
        return [v.key for v in self.violations]

    def __repr__(self) -> str:
        return (
            f"ProtectResult(protected={len(self.protected_keys)}, "
            f"violations={len(self.violations)})"
        )


class EnvProtector:
    """Guards a set of protected keys against deletion or value changes."""

    def __init__(self, protected_keys: List[str]) -> None:
        self._protected: Set[str] = set(protected_keys)

    @property
    def protected_keys(self) -> Set[str]:
        return set(self._protected)

    def check_delete(self, keys_to_delete: List[str]) -> ProtectResult:
        """Return violations for any attempted deletion of protected keys."""
        violations: List[ProtectViolation] = []
        for key in keys_to_delete:
            if key in self._protected:
                violations.append(ProtectViolation(key=key, reason="deletion of protected key"))
        return ProtectResult(protected_keys=self._protected, violations=violations)

    def check_overwrite(
        self,
        current: Dict[str, str],
        proposed: Dict[str, str],
    ) -> ProtectResult:
        """Return violations for any proposed value change on protected keys."""
        violations: List[ProtectViolation] = []
        for key in self._protected:
            if key in current and key in proposed and current[key] != proposed[key]:
                violations.append(
                    ProtectViolation(key=key, reason="overwrite of protected key")
                )
        return ProtectResult(protected_keys=self._protected, violations=violations)

    def filter_safe(
        self,
        proposed: Dict[str, str],
        current: Dict[str, str],
    ) -> Dict[str, str]:
        """Return proposed vars with protected keys restored to their current values."""
        result = dict(proposed)
        for key in self._protected:
            if key in current:
                result[key] = current[key]
        return result
