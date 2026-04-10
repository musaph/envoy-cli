"""Backup and restore support for local .env files."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class BackupEntry:
    key: str
    timestamp: str
    vars: Dict[str, str]
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "timestamp": self.timestamp,
            "vars": self.vars,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackupEntry":
        return cls(
            key=data["key"],
            timestamp=data["timestamp"],
            vars=data["vars"],
            note=data.get("note", ""),
        )

    def __repr__(self) -> str:
        return f"BackupEntry(key={self.key!r}, timestamp={self.timestamp!r}, vars={len(self.vars)})"


class EnvBackupManager:
    def __init__(self, backup_dir: str) -> None:
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.backup_dir / "index.json"
        self._entries: List[BackupEntry] = self._load_index()

    def _load_index(self) -> List[BackupEntry]:
        if not self._index_path.exists():
            return []
        with open(self._index_path, "r", encoding="utf-8") as fh:
            return [BackupEntry.from_dict(d) for d in json.load(fh)]

    def _save_index(self) -> None:
        with open(self._index_path, "w", encoding="utf-8") as fh:
            json.dump([e.to_dict() for e in self._entries], fh, indent=2)

    def create(self, key: str, vars: Dict[str, str], note: str = "") -> BackupEntry:
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = BackupEntry(key=key, timestamp=timestamp, vars=dict(vars), note=note)
        self._entries.append(entry)
        self._save_index()
        return entry

    def list_backups(self, key: Optional[str] = None) -> List[BackupEntry]:
        if key is None:
            return list(self._entries)
        return [e for e in self._entries if e.key == key]

    def restore(self, key: str, index: int = -1) -> Optional[BackupEntry]:
        matches = self.list_backups(key)
        if not matches:
            return None
        return matches[index]

    def delete(self, key: str) -> int:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.key != key]
        self._save_index()
        return before - len(self._entries)
