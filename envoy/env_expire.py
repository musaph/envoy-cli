"""Expiry tracking for environment variables."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ExpiryEntry:
    key: str
    expires_at: datetime
    notify_before_days: int = 7

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "expires_at": self.expires_at.isoformat(),
            "notify_before_days": self.notify_before_days,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExpiryEntry":
        return cls(
            key=data["key"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            notify_before_days=data.get("notify_before_days", 7),
        )

    def __repr__(self) -> str:
        return f"ExpiryEntry(key={self.key!r}, expires_at={self.expires_at.date()})"


@dataclass
class ExpiryViolation:
    key: str
    expires_at: datetime
    expired: bool  # True = already expired, False = expiring soon

    def __repr__(self) -> str:
        status = "expired" if self.expired else "expiring soon"
        return f"ExpiryViolation(key={self.key!r}, status={status!r})"


@dataclass
class ExpiryResult:
    violations: List[ExpiryViolation] = field(default_factory=list)
    checked: int = 0

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)

    @property
    def expired(self) -> List[ExpiryViolation]:
        return [v for v in self.violations if v.expired]

    @property
    def expiring_soon(self) -> List[ExpiryViolation]:
        return [v for v in self.violations if not v.expired]

    def __repr__(self) -> str:
        return (
            f"ExpiryResult(checked={self.checked}, "
            f"expired={len(self.expired)}, expiring_soon={len(self.expiring_soon)})"
        )


class EnvExpiryChecker:
    def __init__(self, entries: Optional[List[ExpiryEntry]] = None) -> None:
        self._entries: Dict[str, ExpiryEntry] = {
            e.key: e for e in (entries or [])
        }

    def register(self, entry: ExpiryEntry) -> None:
        self._entries[entry.key] = entry

    def check(self, vars: Dict[str, str], now: Optional[datetime] = None) -> ExpiryResult:
        if now is None:
            now = datetime.now(timezone.utc)
        violations: List[ExpiryViolation] = []
        checked = 0
        for key in vars:
            if key not in self._entries:
                continue
            checked += 1
            entry = self._entries[key]
            expires_at = entry.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            delta = (expires_at - now).days
            if delta < 0:
                violations.append(ExpiryViolation(key=key, expires_at=expires_at, expired=True))
            elif delta < entry.notify_before_days:
                violations.append(ExpiryViolation(key=key, expires_at=expires_at, expired=False))
        return ExpiryResult(violations=violations, checked=checked)
