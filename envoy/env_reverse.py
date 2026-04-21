from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ReverseChange:
    key: str
    original: str
    reversed_value: str

    def __repr__(self) -> str:
        return f"ReverseChange(key={self.key!r}, original={self.original!r}, reversed={self.reversed_value!r})"


@dataclass
class ReverseResult:
    vars: Dict[str, str] = field(default_factory=dict)
    changes: List[ReverseChange] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return f"ReverseResult(changed={len(self.changes)}, total={len(self.vars)})"


class EnvReverser:
    """Reverses the characters of environment variable values."""

    def __init__(self, keys: List[str] = None):
        """
        Args:
            keys: If provided, only reverse values for these keys.
                  If None, reverse all values.
        """
        self._keys = set(keys) if keys else None

    def reverse(self, vars: Dict[str, str]) -> ReverseResult:
        """Reverse values for matching keys."""
        result_vars: Dict[str, str] = {}
        changes: List[ReverseChange] = []

        for key, value in vars.items():
            if self._keys is None or key in self._keys:
                reversed_value = value[::-1]
                if reversed_value != value:
                    changes.append(ReverseChange(
                        key=key,
                        original=value,
                        reversed_value=reversed_value,
                    ))
                result_vars[key] = reversed_value
            else:
                result_vars[key] = value

        return ReverseResult(vars=result_vars, changes=changes)
