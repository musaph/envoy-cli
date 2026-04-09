"""Lockfile management for envoy-cli.

Tracks a pinned snapshot of resolved env variable names and their
checksum so consumers can detect drift between the stored remote
state and what was last explicitly approved.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


LOCKFILE_NAME = ".envoy-lock.json"


@dataclass
class LockEntry:
    key: str
    checksum: str  # SHA-256 of the value

    def to_dict(self) -> dict:
        return {"key": self.key, "checksum": self.checksum}

    @classmethod
    def from_dict(cls, data: dict) -> "LockEntry":
        return cls(key=data["key"], checksum=data["checksum"])

    @staticmethod
    def compute_checksum(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()


@dataclass
class Lockfile:
    profile: str
    entries: Dict[str, LockEntry] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def update(self, variables: Dict[str, str]) -> None:
        """Rebuild entries from a fresh set of resolved variables."""
        self.entries = {
            key: LockEntry(key=key, checksum=LockEntry.compute_checksum(value))
            for key, value in variables.items()
        }

    def is_stale(self, variables: Dict[str, str]) -> bool:
        """Return True if *variables* differ from the locked state."""
        if set(variables) != set(self.entries):
            return True
        return any(
            LockEntry.compute_checksum(v) != self.entries[k].checksum
            for k, v in variables.items()
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "entries": {k: e.to_dict() for k, e in self.entries.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Lockfile":
        obj = cls(profile=data["profile"])
        obj.entries = {
            k: LockEntry.from_dict(v) for k, v in data.get("entries", {}).items()
        }
        return obj

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def save(self, directory: Path) -> Path:
        path = directory / LOCKFILE_NAME
        path.write_text(json.dumps(self.to_dict(), indent=2))
        return path

    @classmethod
    def load(cls, directory: Path) -> Optional["Lockfile"]:
        path = directory / LOCKFILE_NAME
        if not path.exists():
            return None
        return cls.from_dict(json.loads(path.read_text()))
