"""Read-only enforcement for env variables."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ReadonlyViolation:
    key: str
    old_value: str
    new_value: str

    def __repr__(self) -> str:
        return f"ReadonlyViolation(key={self.key!r}, old={self.old_value!r}, new={self.new_value!r})"


@dataclass
class ReadonlyResult:
    protected: Dict[str, str] = field(default_factory=dict)
    violations: List[ReadonlyViolation] = field(default_factory=list)
    applied: Dict[str, str] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return len(self.violations) == 0

    def __repr__(self) -> str:
        return (
            f"ReadonlyResult(protected={len(self.protected)}, "
            f"violations={len(self.violations)}, "
            f"applied={len(self.applied)})"
        )


class EnvReadonlyGuard:
    """Prevents modification of pinned read-only keys."""

    def __init__(self, readonly_keys: Optional[List[str]] = None) -> None:
        self._readonly: List[str] = [k.upper() for k in (readonly_keys or [])]

    def enforce(
        self,
        base: Dict[str, str],
        incoming: Dict[str, str],
    ) -> ReadonlyResult:
        """Merge *incoming* into *base* while blocking writes to readonly keys.

        Returns a ReadonlyResult whose *applied* dict contains the merged
        variables with readonly keys preserved from *base*.
        """
        violations: List[ReadonlyViolation] = []
        protected: Dict[str, str] = {}
        merged: Dict[str, str] = dict(base)

        for key, new_val in incoming.items():
            upper = key.upper()
            if upper in self._readonly:
                old_val = base.get(key, base.get(upper, ""))
                protected[key] = old_val
                if new_val != old_val:
                    violations.append(
                        ReadonlyViolation(key=key, old_value=old_val, new_value=new_val)
                    )
                # Keep the original value regardless
                merged[key] = old_val
            else:
                merged[key] = new_val

        return ReadonlyResult(
            protected=protected,
            violations=violations,
            applied=merged,
        )

    def list_readonly(self) -> List[str]:
        return list(self._readonly)
