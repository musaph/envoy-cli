"""Build a searchable index of env var keys with position and metadata."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class IndexEntry:
    key: str
    position: int
    value_length: int
    is_empty: bool
    prefix: Optional[str] = None

    def __repr__(self) -> str:
        return f"IndexEntry(key={self.key!r}, pos={self.position}, prefix={self.prefix!r})"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "position": self.position,
            "value_length": self.value_length,
            "is_empty": self.is_empty,
            "prefix": self.prefix,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IndexEntry":
        return cls(
            key=data["key"],
            position=data["position"],
            value_length=data["value_length"],
            is_empty=data["is_empty"],
            prefix=data.get("prefix"),
        )


@dataclass
class IndexResult:
    entries: List[IndexEntry] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"IndexResult(count={len(self.entries)})"

    @property
    def keys(self) -> List[str]:
        return [e.key for e in self.entries]

    @property
    def empty_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.is_empty]

    def by_prefix(self, prefix: str) -> List[IndexEntry]:
        return [e for e in self.entries if e.prefix == prefix]

    def get(self, key: str) -> Optional[IndexEntry]:
        for e in self.entries:
            if e.key == key:
                return e
        return None


class EnvIndexer:
    def __init__(self, prefix_separator: str = "_") -> None:
        self._sep = prefix_separator

    def _extract_prefix(self, key: str) -> Optional[str]:
        parts = key.split(self._sep, 1)
        return parts[0] if len(parts) > 1 else None

    def build(self, vars: Dict[str, str]) -> IndexResult:
        entries = [
            IndexEntry(
                key=key,
                position=idx,
                value_length=len(value),
                is_empty=value == "",
                prefix=self._extract_prefix(key),
            )
            for idx, (key, value) in enumerate(vars.items())
        ]
        return IndexResult(entries=entries)
