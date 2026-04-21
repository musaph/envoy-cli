from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ReplaceChange:
    key: str
    old_value: str
    new_value: str

    def __repr__(self) -> str:
        return f"ReplaceChange(key={self.key!r}, old={self.old_value!r}, new={self.new_value!r})"


@dataclass
class ReplaceResult:
    changes: List[ReplaceChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"ReplaceResult(changes={len(self.changes)}, skipped={len(self.skipped)})"
        )


class EnvReplacer:
    def __init__(self, pattern: str, replacement: str, keys: Optional[List[str]] = None):
        self.pattern = pattern
        self.replacement = replacement
        self.keys = keys  # None means apply to all keys

    def replace(self, vars: Dict[str, str]) -> ReplaceResult:
        changes: List[ReplaceChange] = []
        skipped: List[str] = []
        result: Dict[str, str] = {}

        for key, value in vars.items():
            if self.keys is not None and key not in self.keys:
                result[key] = value
                skipped.append(key)
                continue

            if self.pattern in value:
                new_value = value.replace(self.pattern, self.replacement)
                changes.append(ReplaceChange(key=key, old_value=value, new_value=new_value))
                result[key] = new_value
            else:
                result[key] = value

        return ReplaceResult(changes=changes, skipped=skipped)

    def apply(self, vars: Dict[str, str]) -> Dict[str, str]:
        result_obj = self.replace(vars)
        out = dict(vars)
        for change in result_obj.changes:
            out[change.key] = change.new_value
        return out
