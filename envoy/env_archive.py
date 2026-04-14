"""Archive and restore sets of env variables with timestamps and labels."""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ArchiveEntry:
    label: str
    vars: Dict[str, str]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checksum: str = field(init=False)

    def __post_init__(self) -> None:
        self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        blob = json.dumps(self.vars, sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "vars": self.vars,
            "created_at": self.created_at,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArchiveEntry":
        entry = cls(label=data["label"], vars=data["vars"], created_at=data["created_at"])
        entry.checksum = data.get("checksum", entry.checksum)
        return entry

    def __repr__(self) -> str:
        return f"ArchiveEntry(label={self.label!r}, keys={list(self.vars.keys())}, created_at={self.created_at!r})"


@dataclass
class ArchiveResult:
    entries: List[ArchiveEntry] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"ArchiveResult(entries={len(self.entries)}, errors={len(self.errors)})"


class EnvArchiveManager:
    def __init__(self) -> None:
        self._archives: List[ArchiveEntry] = []

    def save(self, label: str, vars: Dict[str, str]) -> ArchiveEntry:
        entry = ArchiveEntry(label=label, vars=dict(vars))
        self._archives.append(entry)
        return entry

    def restore(self, label: str) -> Optional[Dict[str, str]]:
        for entry in reversed(self._archives):
            if entry.label == label:
                return dict(entry.vars)
        return None

    def list_entries(self) -> List[ArchiveEntry]:
        return list(self._archives)

    def delete(self, label: str) -> bool:
        before = len(self._archives)
        self._archives = [e for e in self._archives if e.label != label]
        return len(self._archives) < before

    def to_dict_list(self) -> List[dict]:
        return [e.to_dict() for e in self._archives]

    def load_from_dict_list(self, data: List[dict]) -> None:
        self._archives = [ArchiveEntry.from_dict(d) for d in data]
