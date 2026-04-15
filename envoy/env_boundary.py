"""Boundary checking for env var values — min/max length and numeric range."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BoundaryViolation:
    key: str
    value: str
    reason: str

    def __repr__(self) -> str:
        return f"BoundaryViolation(key={self.key!r}, reason={self.reason!r})"


@dataclass
class BoundaryResult:
    violations: List[BoundaryViolation] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.violations) == 0

    @property
    def violation_keys(self) -> List[str]:
        return [v.key for v in self.violations]

    def __repr__(self) -> str:
        return (
            f"BoundaryResult(is_clean={self.is_clean}, "
            f"violations={len(self.violations)})"
        )


@dataclass
class BoundaryRule:
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class EnvBoundaryChecker:
    """Check env var values against length and numeric boundary rules."""

    def __init__(self, rules: Optional[Dict[str, BoundaryRule]] = None):
        self._rules: Dict[str, BoundaryRule] = rules or {}

    def add_rule(self, key: str, rule: BoundaryRule) -> None:
        self._rules[key] = rule

    def check(self, vars: Dict[str, str]) -> BoundaryResult:
        violations: List[BoundaryViolation] = []
        for key, value in vars.items():
            rule = self._rules.get(key)
            if rule is None:
                continue
            if rule.min_length is not None and len(value) < rule.min_length:
                violations.append(
                    BoundaryViolation(
                        key=key,
                        value=value,
                        reason=f"length {len(value)} < min_length {rule.min_length}",
                    )
                )
                continue
            if rule.max_length is not None and len(value) > rule.max_length:
                violations.append(
                    BoundaryViolation(
                        key=key,
                        value=value,
                        reason=f"length {len(value)} > max_length {rule.max_length}",
                    )
                )
                continue
            if rule.min_value is not None or rule.max_value is not None:
                try:
                    numeric = float(value)
                except ValueError:
                    violations.append(
                        BoundaryViolation(
                            key=key,
                            value=value,
                            reason="value is not numeric but numeric bounds are set",
                        )
                    )
                    continue
                if rule.min_value is not None and numeric < rule.min_value:
                    violations.append(
                        BoundaryViolation(
                            key=key,
                            value=value,
                            reason=f"{numeric} < min_value {rule.min_value}",
                        )
                    )
                elif rule.max_value is not None and numeric > rule.max_value:
                    violations.append(
                        BoundaryViolation(
                            key=key,
                            value=value,
                            reason=f"{numeric} > max_value {rule.max_value}",
                        )
                    )
        return BoundaryResult(violations=violations)
