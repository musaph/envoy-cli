from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class UppercaseChange:
    original_key: str
    new_key: str

    def __repr__(self) -> str:
        return f"UppercaseChange({self.original_key!r} -> {self.new_key!r})"


@dataclass
class UppercaseResult:
    changes: List[UppercaseChange] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    vars: Dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"UppercaseResult(changes={len(self.changes)}, "
            f"conflicts={len(self.conflicts)})"
        )

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0


class EnvUppercaser:
    """Uppercases all keys in an env var dictionary."""

    def uppercase(self, vars: Dict[str, str]) -> UppercaseResult:
        result_vars: Dict[str, str] = {}
        changes: List[UppercaseChange] = []
        conflicts: List[str] = []

        for key, value in vars.items():
            upper_key = key.upper()
            if upper_key != key:
                if upper_key in result_vars:
                    conflicts.append(upper_key)
                else:
                    changes.append(UppercaseChange(original_key=key, new_key=upper_key))
                    result_vars[upper_key] = value
            else:
                if key in result_vars:
                    conflicts.append(key)
                else:
                    result_vars[key] = value

        return UppercaseResult(changes=changes, conflicts=conflicts, vars=result_vars)
