"""Snapshot management for capturing and restoring .env file states."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Snapshot:
    """Represents a point-in-time capture of environment variables."""

    label: str
    variables: Dict[str, str]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checksum: str = field(init=False)

    def __post_init__(self) -> None:
        self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        payload = json.dumps(self.variables, sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "variables": self.variables,
            "created_at": self.created_at,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        obj = cls(label=data["label"], variables=data["variables"], created_at=data["created_at"])
        obj.checksum = data.get("checksum", obj.checksum)
        return obj

    def __repr__(self) -> str:
        return f"<Snapshot label={self.label!r} vars={len(self.variables)} checksum={self.checksum}>"


class SnapshotManager:
    """Manages a collection of named snapshots in memory or via a JSON store."""

    def __init__(self, store_path: Optional[str] = None) -> None:
        self._store_path = store_path
        self._snapshots: List[Snapshot] = []
        if store_path:
            self._load()

    def capture(self, label: str, variables: Dict[str, str]) -> Snapshot:
        snap = Snapshot(label=label, variables=dict(variables))
        self._snapshots.append(snap)
        if self._store_path:
            self._save()
        return snap

    def get(self, label: str) -> Optional[Snapshot]:
        for snap in reversed(self._snapshots):
            if snap.label == label:
                return snap
        return None

    def list_snapshots(self) -> List[Snapshot]:
        return list(self._snapshots)

    def delete(self, label: str) -> bool:
        before = len(self._snapshots)
        self._snapshots = [s for s in self._snapshots if s.label != label]
        removed = len(self._snapshots) < before
        if removed and self._store_path:
            self._save()
        return removed

    def _save(self) -> None:
        import pathlib
        data = [s.to_dict() for s in self._snapshots]
        pathlib.Path(self._store_path).write_text(json.dumps(data, indent=2))

    def _load(self) -> None:
        import pathlib
        p = pathlib.Path(self._store_path)
        if p.exists():
            data = json.loads(p.read_text())
            self._snapshots = [Snapshot.from_dict(d) for d in data]
