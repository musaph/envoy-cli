"""Audit log for tracking push/pull/delete operations on env files."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


AUDIT_LOG_FILENAME = "audit.log"


class AuditEntry:
    """Represents a single audit log entry."""

    def __init__(self, action: str, key: str, environment: str, user: Optional[str] = None):
        self.action = action
        self.key = key
        self.environment = environment
        self.user = user or os.environ.get("USER", "unknown")
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "key": self.key,
            "environment": self.environment,
            "user": self.user,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        entry = cls(
            action=data["action"],
            key=data["key"],
            environment=data["environment"],
            user=data.get("user", "unknown"),
        )
        entry.timestamp = data["timestamp"]
        return entry

    def __repr__(self) -> str:
        return f"[{self.timestamp}] {self.action.upper()} {self.key} ({self.environment}) by {self.user}"


class AuditLog:
    """Manages audit log persistence and retrieval."""

    def __init__(self, log_dir: str):
        self.log_path = Path(log_dir) / AUDIT_LOG_FILENAME
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, action: str, key: str, environment: str, user: Optional[str] = None) -> AuditEntry:
        entry = AuditEntry(action=action, key=key, environment=environment, user=user)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def read_all(self) -> List[AuditEntry]:
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(AuditEntry.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError):
                        continue
        return entries

    def filter_by_environment(self, environment: str) -> List[AuditEntry]:
        return [e for e in self.read_all() if e.environment == environment]

    def filter_by_action(self, action: str) -> List[AuditEntry]:
        return [e for e in self.read_all() if e.action == action]

    def clear(self) -> None:
        if self.log_path.exists():
            self.log_path.unlink()
