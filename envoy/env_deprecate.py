"""Deprecation tracking for environment variables."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DeprecationEntry:
    key: str
    reason: str
    replacement: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "reason": self.reason,
            "replacement": self.replacement,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeprecationEntry":
        return cls(
            key=data["key"],
            reason=data["reason"],
            replacement=data.get("replacement"),
        )

    def __repr__(self) -> str:
        suffix = f" -> {self.replacement}" if self.replacement else ""
        return f"DeprecationEntry({self.key!r}{suffix})"


@dataclass
class DeprecationResult:
    deprecated: List[DeprecationEntry] = field(default_factory=list)
    present_keys: List[str] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.present_keys)

    def __repr__(self) -> str:
        return (
            f"DeprecationResult(violations={len(self.present_keys)}, "
            f"registered={len(self.deprecated)})"
        )


class EnvDeprecationChecker:
    def __init__(self, entries: Optional[List[DeprecationEntry]] = None):
        self._entries: Dict[str, DeprecationEntry] = {
            e.key: e for e in (entries or [])
        }

    def register(self, key: str, reason: str, replacement: Optional[str] = None) -> None:
        self._entries[key] = DeprecationEntry(key=key, reason=reason, replacement=replacement)

    def check(self, vars: Dict[str, str]) -> DeprecationResult:
        present = [
            self._entries[k]
            for k in vars
            if k in self._entries
        ]
        return DeprecationResult(
            deprecated=list(self._entries.values()),
            present_keys=[e.key for e in present],
        )

    def suggestions(self, vars: Dict[str, str]) -> Dict[str, Optional[str]]:
        """Return {old_key: replacement_key} for deprecated keys found in vars."""
        return {
            k: self._entries[k].replacement
            for k in vars
            if k in self._entries
        }
