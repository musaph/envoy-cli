from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CountResult:
    total: int = 0
    set_count: int = 0
    empty_count: int = 0
    by_prefix: Dict[str, int] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"CountResult(total={self.total}, set={self.set_count}, "
            f"empty={self.empty_count})"
        )

    @property
    def unset_ratio(self) -> float:
        if self.total == 0:
            return 0.0
        return self.empty_count / self.total


class EnvCounter:
    """Counts and summarises variables in an env mapping."""

    def __init__(self, prefix_delimiters: Optional[List[str]] = None) -> None:
        self._delimiters = prefix_delimiters or ["_"]

    def count(self, vars: Dict[str, str]) -> CountResult:
        total = len(vars)
        empty_count = sum(1 for v in vars.values() if v.strip() == "")
        set_count = total - empty_count
        by_prefix = self._count_by_prefix(vars)
        return CountResult(
            total=total,
            set_count=set_count,
            empty_count=empty_count,
            by_prefix=by_prefix,
        )

    def _count_by_prefix(self, vars: Dict[str, str]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for key in vars:
            prefix = self._extract_prefix(key)
            if prefix:
                counts[prefix] = counts.get(prefix, 0) + 1
        return counts

    def _extract_prefix(self, key: str) -> Optional[str]:
        for delimiter in self._delimiters:
            if delimiter in key:
                return key.split(delimiter)[0]
        return None
