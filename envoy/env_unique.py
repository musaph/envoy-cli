from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class UniqueChange:
    key: str
    duplicate_count: int

    def __repr__(self) -> str:
        return f"UniqueChange(key={self.key!r}, duplicates={self.duplicate_count})"


@dataclass
class UniqueResult:
    original: Dict[str, str]
    deduped: Dict[str, str]
    changes: List[UniqueChange] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"UniqueResult(total={len(self.original)}, removed={self.removed_count})"

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def removed_count(self) -> int:
        return len(self.original) - len(self.deduped)

    @property
    def duplicate_keys(self) -> List[str]:
        return [c.key for c in self.changes]


class EnvUniqueFilter:
    """Removes duplicate values, keeping the first occurrence of each unique value."""

    def __init__(self, case_sensitive: bool = True):
        self.case_sensitive = case_sensitive

    def filter(self, vars: Dict[str, str]) -> UniqueResult:
        seen_values: Dict[str, str] = {}
        deduped: Dict[str, str] = {}
        changes: List[UniqueChange] = []
        value_counts: Dict[str, int] = {}

        for key, value in vars.items():
            normalized = value if self.case_sensitive else value.lower()
            value_counts[normalized] = value_counts.get(normalized, 0) + 1

        for key, value in vars.items():
            normalized = value if self.case_sensitive else value.lower()
            if normalized not in seen_values:
                seen_values[normalized] = key
                deduped[key] = value
            else:
                changes.append(UniqueChange(key=key, duplicate_count=value_counts[normalized] - 1))

        return UniqueResult(original=dict(vars), deduped=deduped, changes=changes)
