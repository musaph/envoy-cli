from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class VersionEntry:
    version: int
    vars: Dict[str, str]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "vars": dict(self.vars),
            "created_at": self.created_at,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VersionEntry":
        return cls(
            version=data["version"],
            vars=data.get("vars", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            label=data.get("label"),
        )

    def __repr__(self) -> str:
        label_part = f" ({self.label})" if self.label else ""
        return f"<VersionEntry v{self.version}{label_part} keys={len(self.vars)}>"


@dataclass
class VersionResult:
    entries: List[VersionEntry] = field(default_factory=list)

    @property
    def latest(self) -> Optional[VersionEntry]:
        return max(self.entries, key=lambda e: e.version) if self.entries else None

    @property
    def count(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return f"<VersionResult versions={self.count}>"


class EnvVersionManager:
    def __init__(self, max_versions: int = 10):
        self._max = max_versions
        self._entries: List[VersionEntry] = []

    def save(self, vars: Dict[str, str], label: Optional[str] = None) -> VersionEntry:
        next_version = (self._entries[-1].version + 1) if self._entries else 1
        entry = VersionEntry(version=next_version, vars=dict(vars), label=label)
        self._entries.append(entry)
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max:]
        return entry

    def get(self, version: int) -> Optional[VersionEntry]:
        for entry in self._entries:
            if entry.version == version:
                return entry
        return None

    def list(self) -> VersionResult:
        return VersionResult(entries=list(self._entries))

    def rollback(self, version: int) -> Optional[Dict[str, str]]:
        entry = self.get(version)
        return dict(entry.vars) if entry else None
