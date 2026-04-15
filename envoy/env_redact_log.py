"""Redact sensitive values from audit log entries before display or export."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from envoy.secrets import SecretScanner


@dataclass
class RedactLogChange:
    key: str
    original_value: str
    redacted_value: str

    def __repr__(self) -> str:
        return f"RedactLogChange(key={self.key!r})"


@dataclass
class RedactLogResult:
    changes: List[RedactLogChange] = field(default_factory=list)
    redacted: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"RedactLogResult(changes={len(self.changes)}, "
            f"has_changes={self.has_changes})"
        )


class EnvRedactLog:
    """Redacts sensitive variable values in a dict, suitable for safe logging."""

    MASK = "***REDACTED***"

    def __init__(self, scanner: SecretScanner | None = None) -> None:
        self._scanner = scanner or SecretScanner()

    def redact(self, vars: Dict[str, str]) -> RedactLogResult:
        """Return a RedactLogResult with sensitive values masked."""
        changes: List[RedactLogChange] = []
        redacted: Dict[str, str] = {}

        for key, value in vars.items():
            if self._scanner.is_sensitive_key(key):
                changes.append(RedactLogChange(
                    key=key,
                    original_value=value,
                    redacted_value=self.MASK,
                ))
                redacted[key] = self.MASK
            else:
                redacted[key] = value

        return RedactLogResult(changes=changes, redacted=redacted)
