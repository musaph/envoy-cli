"""Flatten nested key naming conventions (e.g. APP__DB__HOST -> APP_DB_HOST)."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FlattenKeyChange:
    original: str
    flattened: str

    def __repr__(self) -> str:
        return f"FlattenKeyChange({self.original!r} -> {self.flattened!r})"


@dataclass
class FlattenKeyResult:
    vars: Dict[str, str]
    changes: List[FlattenKeyChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.original for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"FlattenKeyResult(changed={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvKeyFlattener:
    """Flatten double-underscore (or custom) separators in env var keys."""

    def __init__(self, replacement: str = "_",
                 overwrite: bool = False):
        self.separator = separator
        self.replacement = replacement
        self.overwrite = overwrite

    def flatten(self, vars: Dict[str, str]) -> FlattenKeyResult:
        result_vars: Dict[str, str] = {}
        changes: List[FlattenKeyChange] = []
        skipped: List[str] = []

        for key, value in vars.items():
            if self.separator in key:
                new_key = key.replace(self.separator, self.replacement)
                if new_key in result_vars or new_key in vars:
                    if not self.overwrite:
                        skipped.append(key)
                        result_vars[key] = value
                        continue
                changes.append(FlattenKeyChange(original=key, flattened=new_key))
                result_vars[new_key] = value
            else:
                result_vars[key] = value

        return FlattenKeyResult(vars=result_vars, changes=changes, skipped=skipped)
