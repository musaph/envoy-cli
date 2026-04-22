from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NumericChange:
    key: str
    original: str
    converted: str
    operation: str  # 'round', 'abs', 'negate', 'increment', 'decrement'

    def __repr__(self) -> str:
        return f"NumericChange(key={self.key!r}, op={self.operation!r}, {self.original!r} -> {self.converted!r})"


@dataclass
class NumericResult:
    changes: List[NumericChange] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"NumericResult(changes={len(self.changes)}, "
            f"errors={len(self.errors)}, skipped={len(self.skipped)})"
        )


class EnvNumeric:
    """Apply numeric operations to env var values."""

    OPERATIONS = ("round", "abs", "negate", "increment", "decrement")

    def __init__(self, operation: str = "round", precision: int = 0,
                 step: float = 1.0, keys: Optional[List[str]] = None):
        if operation not in self.OPERATIONS:
            raise ValueError(f"Unknown operation {operation!r}. Choose from {self.OPERATIONS}")
        self.operation = operation
        self.precision = precision
        self.step = step
        self.keys = keys  # None means apply to all numeric-looking values

    def _apply(self, value: str) -> Optional[str]:
        try:
            num = float(value)
        except ValueError:
            return None

        if self.operation == "round":
            result = round(num, self.precision)
            return str(int(result)) if self.precision == 0 else str(result)
        elif self.operation == "abs":
            result = abs(num)
        elif self.operation == "negate":
            result = -num
        elif self.operation == "increment":
            result = num + self.step
        elif self.operation == "decrement":
            result = num - self.step
        else:
            return None

        return str(int(result)) if result == int(result) else str(result)

    def process(self, vars: Dict[str, str]) -> NumericResult:
        result = NumericResult()
        for key, value in vars.items():
            if self.keys is not None and key not in self.keys:
                result.skipped.append(key)
                continue
            converted = self._apply(value)
            if converted is None:
                result.skipped.append(key)
                continue
            if converted != value:
                result.changes.append(NumericChange(
                    key=key, original=value,
                    converted=converted, operation=self.operation
                ))
        return result

    def apply(self, vars: Dict[str, str]) -> Dict[str, str]:
        result = self.process(vars)
        out = dict(vars)
        for change in result.changes:
            out[change.key] = change.converted
        return out
