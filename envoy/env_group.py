"""Group environment variables by prefix or custom rules."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GroupResult:
    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:
        n_groups = len(self.groups)
        n_ungrouped = len(self.ungrouped)
        return f"<GroupResult groups={n_groups} ungrouped={n_ungrouped}>"

    @property
    def all_vars(self) -> Dict[str, str]:
        """Return all variables, grouped and ungrouped, in a flat dict."""
        merged: Dict[str, str] = {}
        for vars_ in self.groups.values():
            merged.update(vars_)
        merged.update(self.ungrouped)
        return merged


class EnvGrouper:
    """Groups env vars by shared key prefix (e.g. DB_, AWS_)."""

    def __init__(self, min_group_size: int = 1, separator: str = "_") -> None:
        self.min_group_size = min_group_size
        self.separator = separator

    def group_by_prefix(self
        , vars_: Dict[str, str]
        , prefixes: Optional[List[str]] = None
    ) -> GroupResult:
        """Group variables by explicit prefixes or auto-detect from keys."""
        if prefixes is None:
            prefixes = self._detect_prefixes(vars_)

        groups: Dict[str, Dict[str, str]] = {p: {} for p in prefixes}
        ungrouped: Dict[str, str] = {}

        for key, value in vars_.items():
            matched = False
            for prefix in prefixes:
                if key.startswith(prefix + self.separator) or key == prefix:
                    groups[prefix][key] = value
                    matched = True
                    break
            if not matched:
                ungrouped[key] = value

        # Remove empty groups
        groups = {p: v for p, v in groups.items() if v}
        return GroupResult(groups=groups, ungrouped=ungrouped)

    def _detect_prefixes(self, vars_: Dict[str, str]) -> List[str]:
        """Auto-detect common prefixes from variable names."""
        prefix_counts: Dict[str, int] = {}
        for key in vars_:
            if self.separator in key:
                prefix = key.split(self.separator)[0]
                prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        return [
            p for p, count in prefix_counts.items()
            if count >= self.min_group_size
        ]
