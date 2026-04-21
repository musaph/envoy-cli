"""Strip prefix or suffix from environment variable values."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StripChange:
    key: str
    old_value: str
    new_value: str

    def __repr__(self) -> str:
        return f"StripChange(key={self.key!r}, old={self.old_value!r}, new={self.new_value!r})"


@dataclass
class StripResult:
    changes: List[StripChange] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"StripResult(changes={len(self.changes)}, "
            f"unchanged={len(self.unchanged)})"
        )


class EnvStripper:
    """Strip a prefix and/or suffix from environment variable values."""

    def __init__(
        self,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        keys: Optional[List[str]] = None,
    ) -> None:
        self.prefix = prefix
        self.suffix = suffix
        self.keys = keys  # None means apply to all keys

    def strip(self, vars: Dict[str, str]) -> StripResult:
        changes: List[StripChange] = []
        unchanged: List[str] = []

        for key, value in vars.items():
            if self.keys is not None and key not in self.keys:
                unchanged.append(key)
                continue

            new_value = value
            if self.prefix and new_value.startswith(self.prefix):
                new_value = new_value[len(self.prefix):]
            if self.suffix and new_value.endswith(self.suffix):
                new_value = new_value[: len(new_value) - len(self.suffix)]

            if new_value != value:
                changes.append(StripChange(key=key, old_value=value, new_value=new_value))
            else:
                unchanged.append(key)

        return StripResult(changes=changes, unchanged=unchanged)

    def apply(self, vars: Dict[str, str]) -> Dict[str, str]:
        result = self.strip(vars)
        out = dict(vars)
        for change in result.changes:
            out[change.key] = change.new_value
        return out
