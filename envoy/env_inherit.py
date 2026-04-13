"""Env inheritance: merge a base env into a child, respecting override rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InheritChange:
    key: str
    source: str          # 'base' | 'child' | 'merged'
    base_value: Optional[str]
    child_value: Optional[str]
    final_value: str

    def __repr__(self) -> str:
        return (
            f"InheritChange(key={self.key!r}, source={self.source!r}, "
            f"final={self.final_value!r})"
        )


@dataclass
class InheritResult:
    vars: Dict[str, str] = field(default_factory=dict)
    changes: List[InheritChange] = field(default_factory=list)

    @property
    def has_overrides(self) -> bool:
        return any(c.source == 'child' for c in self.changes)

    @property
    def inherited_keys(self) -> List[str]:
        return [c.key for c in self.changes if c.source == 'base']

    def __repr__(self) -> str:
        return (
            f"InheritResult(total={len(self.vars)}, "
            f"overrides={sum(1 for c in self.changes if c.source == 'child')})"
        )


class EnvInheritor:
    """Merge *base* vars into *child* vars; child keys always win."""

    def __init__(self, allow_empty_override: bool = True):
        self.allow_empty_override = allow_empty_override

    def inherit(
        self,
        base: Dict[str, str],
        child: Dict[str, str],
    ) -> InheritResult:
        merged: Dict[str, str] = {}
        changes: List[InheritChange] = []

        all_keys = list(base.keys()) + [k for k in child if k not in base]

        for key in all_keys:
            in_base = key in base
            in_child = key in child

            if in_child and in_base:
                child_val = child[key]
                if not self.allow_empty_override and child_val == "":
                    final = base[key]
                    source = "base"
                else:
                    final = child_val
                    source = "child"
            elif in_child:
                final = child[key]
                source = "child"
            else:
                final = base[key]
                source = "base"

            merged[key] = final
            changes.append(
                InheritChange(
                    key=key,
                    source=source,
                    base_value=base.get(key),
                    child_value=child.get(key),
                    final_value=final,
                )
            )

        return InheritResult(vars=merged, changes=changes)
