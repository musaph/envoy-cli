from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TypeViolation:
    key: str
    expected_type: str
    actual_value: str
    reason: str

    def __repr__(self) -> str:
        return f"TypeViolation(key={self.key!r}, expected={self.expected_type!r}, value={self.actual_value!r})"


@dataclass
class TypeCheckResult:
    violations: List[TypeViolation] = field(default_factory=list)
    checked: int = 0

    @property
    def is_clean(self) -> bool:
        return len(self.violations) == 0

    def __repr__(self) -> str:
        return f"TypeCheckResult(checked={self.checked}, violations={len(self.violations)})"


TYPE_VALIDATORS = {
    "int": lambda v: v.lstrip("-").isdigit(),
    "float": lambda v: _is_float(v),
    "bool": lambda v: v.lower() in ("true", "false", "1", "0", "yes", "no"),
    "url": lambda v: v.startswith(("http://", "https://")),
    "nonempty": lambda v: len(v.strip()) > 0,
}


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


class EnvTypeChecker:
    def __init__(self, schema: Dict[str, str]):
        """schema maps key -> expected type string (e.g. 'int', 'bool', 'url')."""
        self._schema = schema

    def check(self, vars: Dict[str, str]) -> TypeCheckResult:
        violations: List[TypeViolation] = []
        checked = 0
        for key, expected_type in self._schema.items():
            if key not in vars:
                continue
            checked += 1
            value = vars[key]
            validator = TYPE_VALIDATORS.get(expected_type)
            if validator is None:
                continue
            if not validator(value):
                violations.append(
                    TypeViolation(
                        key=key,
                        expected_type=expected_type,
                        actual_value=value,
                        reason=f"Value {value!r} is not a valid {expected_type}",
                    )
                )
        return TypeCheckResult(violations=violations, checked=checked)
