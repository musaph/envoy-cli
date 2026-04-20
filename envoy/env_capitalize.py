from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class CapitalizeChange:
    key: str
    old_value: str
    new_value: str

    def __repr__(self) -> str:
        return f"CapitalizeChange(key={self.key!r}, {self.old_value!r} -> {self.new_value!r})"


@dataclass
class CapitalizeResult:
    vars: Dict[str, str]
    changes: List[CapitalizeChange] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"CapitalizeResult(total={len(self.vars)}, changed={len(self.changes)})"

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]


class EnvCapitalizer:
    """Capitalizes the first letter of each env var value."""

    def __init__(self, only_keys: List[str] = None) -> None:
        self.only_keys = set(only_keys) if only_keys else None

    def capitalize(self, vars: Dict[str, str]) -> CapitalizeResult:
        result: Dict[str, str] = {}
        changes: List[CapitalizeChange] = []

        for key, value in vars.items():
            if self.only_keys is not None and key not in self.only_keys:
                result[key] = value
                continue

            new_value = value.capitalize() if value else value
            result[key] = new_value

            if new_value != value:
                changes.append(CapitalizeChange(key=key, old_value=value, new_value=new_value))

        return CapitalizeResult(vars=result, changes=changes)
