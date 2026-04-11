"""Pin specific env var keys to required values or patterns."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class PinViolation:
    key: str
    expected: str
    actual: Optional[str]
    reason: str

    def __repr__(self) -> str:
        return f"PinViolation(key={self.key!r}, reason={self.reason!r})"


@dataclass
class PinResult:
    violations: List[PinViolation] = field(default_factory=list)
    pinned_count: int = 0

    @property
    def is_clean(self) -> bool:
        return len(self.violations) == 0

    def __repr__(self) -> str:
        return (
            f"PinResult(pinned={self.pinned_count}, "
            f"violations={len(self.violations)}, clean={self.is_clean})"
        )


class EnvPinner:
    """Validates that specific env vars are pinned to expected values or patterns."""

    def __init__(self, pins: Dict[str, str]) -> None:
        """
        Args:
            pins: Mapping of key -> expected value or regex pattern (prefix with 're:').
        """
        self._pins = pins

    def check(self, vars: Dict[str, str]) -> PinResult:
        violations: List[PinViolation] = []
        for key, expected in self._pins.items():
            actual = vars.get(key)
            if actual is None:
                violations.append(
                    PinViolation(key=key, expected=expected, actual=None,
                                 reason="key missing")
                )
            elif expected.startswith("re:"):
                pattern = expected[3:]
                if not re.fullmatch(pattern, actual):
                    violations.append(
                        PinViolation(key=key, expected=expected, actual=actual,
                                     reason="value does not match pattern")
                    )
            elif actual != expected:
                violations.append(
                    PinViolation(key=key, expected=expected, actual=actual,
                                 reason="value mismatch")
                )
        return PinResult(violations=violations, pinned_count=len(self._pins))

    def apply(self, vars: Dict[str, str]) -> Dict[str, str]:
        """Return a copy of vars with pinned keys forced to their exact values.
        Pattern pins (re:) are skipped — only literal pins are applied."""
        result = dict(vars)
        for key, expected in self._pins.items():
            if not expected.startswith("re:"):
                result[key] = expected
        return result
