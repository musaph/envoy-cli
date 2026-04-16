from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LowercaseChange:
    key: str
    old_key: str
    value: str

    def __repr__(self) -> str:
        return f"LowercaseChange({self.old_key!r} -> {self.key!r})"


@dataclass
class LowercaseResult:
    changes: List[LowercaseChange] = field(default_factory=list)
    vars: Dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"LowercaseResult(changes={len(self.changes)}, vars={len(self.vars)})"

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.old_key for c in self.changes]


class EnvLowercaser:
    def __init__(self, overwrite: bool = False):
        """
        :param overwrite: If True, overwrite existing lowercase key when a
                          collision occurs. If False, skip the rename.
        """
        self.overwrite = overwrite

    def lowercase(self, vars: Dict[str, str]) -> LowercaseResult:
        """Return a new vars dict with all keys lowercased."""
        result_vars: Dict[str, str] = {}
        changes: List[LowercaseChange] = []

        for key, value in vars.items():
            new_key = key.lower()
            if new_key == key:
                result_vars[key] = value
                continue

            if new_key in result_vars and not self.overwrite:
                # Keep original key untouched on collision without overwrite
                result_vars[key] = value
                continue

            changes.append(LowercaseChange(key=new_key, old_key=key, value=value))
            result_vars[new_key] = value

        return LowercaseResult(changes=changes, vars=result_vars)
