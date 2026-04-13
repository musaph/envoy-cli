from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PrefixChange:
    key: str
    new_key: str
    value: str

    def __repr__(self) -> str:
        return f"PrefixChange({self.key!r} -> {self.new_key!r})"


@dataclass
class PrefixResult:
    original: Dict[str, str]
    renamed: Dict[str, str]
    changes: List[PrefixChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def __repr__(self) -> str:
        return (
            f"PrefixResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvPrefixer:
    def __init__(self, prefix: str, separator: str = "_"):
        if not prefix:
            raise ValueError("Prefix must not be empty")
        self.prefix = prefix.upper()
        self.separator = separator

    def add(self, vars_: Dict[str, str]) -> PrefixResult:
        """Add prefix to all keys that don't already have it."""
        renamed: Dict[str, str] = {}
        changes: List[PrefixChange] = []
        skipped: List[str] = []
        full_prefix = self.prefix + self.separator

        for key, value in vars_.items():
            if key.startswith(full_prefix):
                renamed[key] = value
                skipped.append(key)
            else:
                new_key = full_prefix + key
                renamed[new_key] = value
                changes.append(PrefixChange(key=key, new_key=new_key, value=value))

        return PrefixResult(
            original=dict(vars_),
            renamed=renamed,
            changes=changes,
            skipped=skipped,
        )

    def remove(self, vars_: Dict[str, str]) -> PrefixResult:
        """Remove prefix from all keys that have it."""
        renamed: Dict[str, str] = {}
        changes: List[PrefixChange] = []
        skipped: List[str] = []
        full_prefix = self.prefix + self.separator

        for key, value in vars_.items():
            if key.startswith(full_prefix):
                new_key = key[len(full_prefix):]
                renamed[new_key] = value
                changes.append(PrefixChange(key=key, new_key=new_key, value=value))
            else:
                renamed[key] = value
                skipped.append(key)

        return PrefixResult(
            original=dict(vars_),
            renamed=renamed,
            changes=changes,
            skipped=skipped,
        )

    def filter(self, vars_: Dict[str, str]) -> Dict[str, str]:
        """Return only vars that have the prefix."""
        full_prefix = self.prefix + self.separator
        return {k: v for k, v in vars_.items() if k.startswith(full_prefix)}
