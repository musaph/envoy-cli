"""Freeze and unfreeze environment variable sets to prevent accidental changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class FreezeViolation:
    key: str
    expected: str
    actual: str

    def __repr__(self) -> str:
        return f"FreezeViolation(key={self.key!r}, expected={self.expected!r}, actual={self.actual!r})"


@dataclass
class FreezeResult:
    frozen_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    vars: Dict[str, str] = field(default_factory=dict)
    violations: List[FreezeViolation] = field(default_factory=list)
    is_clean: bool = True

    def __repr__(self) -> str:
        return (
            f"FreezeResult(vars={len(self.vars)}, "
            f"violations={len(self.violations)}, is_clean={self.is_clean})"
        )

    def to_dict(self) -> dict:
        return {
            "frozen_at": self.frozen_at,
            "vars": self.vars,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FreezeResult":
        return cls(
            frozen_at=data.get("frozen_at", ""),
            vars=data.get("vars", {}),
        )


class EnvFreezer:
    """Freeze a snapshot of env vars and verify them later."""

    def freeze(self, vars: Dict[str, str]) -> FreezeResult:
        """Capture a frozen snapshot of the given vars."""
        return FreezeResult(vars=dict(vars))

    def check(self, frozen: FreezeResult, current: Dict[str, str]) -> FreezeResult:
        """Compare current vars against a frozen snapshot."""
        violations: List[FreezeViolation] = []

        for key, expected in frozen.vars.items():
            actual = current.get(key)
            if actual is None:
                violations.append(FreezeViolation(key=key, expected=expected, actual="<missing>"))
            elif actual != expected:
                violations.append(FreezeViolation(key=key, expected=expected, actual=actual))

        for key in current:
            if key not in frozen.vars:
                violations.append(FreezeViolation(key=key, expected="<absent>", actual=current[key]))

        result = FreezeResult(
            frozen_at=frozen.frozen_at,
            vars=frozen.vars,
            violations=violations,
            is_clean=len(violations) == 0,
        )
        return result
