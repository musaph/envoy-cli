from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ReorderChange:
    key: str
    old_index: int
    new_index: int

    def __repr__(self) -> str:
        return f"ReorderChange(key={self.key!r}, {self.old_index} -> {self.new_index})"


@dataclass
class ReorderResult:
    original: Dict[str, str]
    reordered: Dict[str, str]
    changes: List[ReorderChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    def __repr__(self) -> str:
        return f"ReorderResult(changes={len(self.changes)})"


class EnvReorderer:
    def __init__(self, order: Optional[List[str]] = None, alphabetical: bool = False):
        self.order = order or []
        self.alphabetical = alphabetical

    def reorder(self, vars: Dict[str, str]) -> ReorderResult:
        original_keys = list(vars.keys())

        if self.alphabetical:
            sorted_keys = sorted(vars.keys())
        elif self.order:
            known = [k for k in self.order if k in vars]
            remaining = [k for k in vars if k not in self.order]
            sorted_keys = known + remaining
        else:
            return ReorderResult(original=vars, reordered=dict(vars), changes=[])

        reordered = {k: vars[k] for k in sorted_keys}

        changes = [
            ReorderChange(key=k, old_index=original_keys.index(k), new_index=i)
            for i, k in enumerate(sorted_keys)
            if original_keys.index(k) != i
        ]

        return ReorderResult(original=vars, reordered=reordered, changes=changes)
