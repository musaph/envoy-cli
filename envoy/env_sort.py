"""Sorting and grouping utilities for .env variable collections."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class GroupBy(str, Enum):
    PREFIX = "prefix"
    NONE = "none"


@dataclass
class SortResult:
    sorted_vars: Dict[str, str]
    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    original_count: int = 0
    sorted_count: int = 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<SortResult vars={self.sorted_count} groups={len(self.groups)}>"
        )


class EnvSorter:
    """Sort and optionally group environment variables."""

    def __init__(
        self,
        order: SortOrder = SortOrder.ASC,
        group_by: GroupBy = GroupBy.NONE,
        prefix_separator: str = "_",
    ) -> None:
        self.order = order
        self.group_by = group_by
        self.prefix_separator = prefix_separator

    def sort(self, vars: Dict[str, str]) -> SortResult:
        """Return a SortResult with variables sorted by key."""
        reverse = self.order == SortOrder.DESC
        sorted_vars: Dict[str, str] = dict(
            sorted(vars.items(), key=lambda kv: kv[0], reverse=reverse)
        )
        groups: Dict[str, Dict[str, str]] = {}
        if self.group_by == GroupBy.PREFIX:
            groups = self._group_by_prefix(sorted_vars)
        return SortResult(
            sorted_vars=sorted_vars,
            groups=groups,
            original_count=len(vars),
            sorted_count=len(sorted_vars),
        )

    def _group_by_prefix(self, vars: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        groups: Dict[str, Dict[str, str]] = {}
        for key, value in vars.items():
            if self.prefix_separator in key:
                prefix = key.split(self.prefix_separator, 1)[0]
            else:
                prefix = "__other__"
            groups.setdefault(prefix, {})[key] = value
        return groups

    def sort_keys_in_group(
        self, group: Dict[str, str], order: Optional[SortOrder] = None
    ) -> Dict[str, str]:
        """Sort a single group dict, optionally overriding the default order."""
        reverse = (order or self.order) == SortOrder.DESC
        return dict(sorted(group.items(), key=lambda kv: kv[0], reverse=reverse))
