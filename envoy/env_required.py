"""Check and enforce required environment variable definitions."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RequiredViolation:
    key: str
    reason: str

    def __repr__(self) -> str:
        return f"RequiredViolation(key={self.key!r}, reason={self.reason!r})"


@dataclass
class RequiredResult:
    missing: List[RequiredViolation] = field(default_factory=list)
    empty: List[RequiredViolation] = field(default_factory=list)

    @property
    def is_satisfied(self) -> bool:
        return not self.missing and not self.empty

    @property
    def violations(self) -> List[RequiredViolation]:
        return self.missing + self.empty

    def __repr__(self) -> str:
        return (
            f"RequiredResult(missing={len(self.missing)}, "
            f"empty={len(self.empty)}, satisfied={self.is_satisfied})"
        )


class EnvRequiredChecker:
    """Validates that a set of required keys are present and non-empty."""

    def __init__(self, required_keys: List[str], allow_empty: bool = False):
        self._required = list(required_keys)
        self._allow_empty = allow_empty

    def check(self, vars: Dict[str, str]) -> RequiredResult:
        """Return a RequiredResult describing any violations."""
        result = RequiredResult()
        for key in self._required:
            if key not in vars:
                result.missing.append(
                    RequiredViolation(key=key, reason="key not present")
                )
            elif not self._allow_empty and vars[key].strip() == "":
                result.empty.append(
                    RequiredViolation(key=key, reason="value is empty")
                )
        return result

    def missing_keys(self, vars: Dict[str, str]) -> List[str]:
        """Return only the names of missing keys."""
        return [k for k in self._required if k not in vars]

    def empty_keys(self, vars: Dict[str, str]) -> List[str]:
        """Return names of keys present but empty (when allow_empty is False)."""
        if self._allow_empty:
            return []
        return [
            k for k in self._required
            if k in vars and vars[k].strip() == ""
        ]
