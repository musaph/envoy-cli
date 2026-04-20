"""Base64 encoding/decoding for env variable values."""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Base64Change:
    key: str
    original: str
    result: str
    operation: str  # 'encode' or 'decode'
    error: Optional[str] = None

    def __repr__(self) -> str:
        if self.error:
            return f"Base64Change(key={self.key!r}, op={self.operation!r}, error={self.error!r})"
        return f"Base64Change(key={self.key!r}, op={self.operation!r})"


@dataclass
class Base64Result:
    changes: List[Base64Change] = field(default_factory=list)
    vars: Dict[str, str] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return any(c.error is None for c in self.changes)

    def has_errors(self) -> bool:
        return any(c.error is not None for c in self.changes)

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes if c.error is None]

    def error_keys(self) -> List[str]:
        return [c.key for c in self.changes if c.error is not None]

    def __repr__(self) -> str:
        return (
            f"Base64Result(changed={len(self.changed_keys())}, "
            f"errors={len(self.error_keys())})"
        )


class EnvBase64Processor:
    """Encode or decode env variable values using Base64."""

    def __init__(self, keys: Optional[List[str]] = None) -> None:
        self._keys = keys  # None means process all keys

    def _should_process(self, key: str) -> bool:
        return self._keys is None or key in self._keys

    def encode(self, vars: Dict[str, str]) -> Base64Result:
        """Base64-encode selected variable values."""
        result_vars = dict(vars)
        changes: List[Base64Change] = []
        for key, value in vars.items():
            if not self._should_process(key):
                continue
            encoded = base64.b64encode(value.encode()).decode()
            result_vars[key] = encoded
            changes.append(Base64Change(key=key, original=value, result=encoded, operation="encode"))
        return Base64Result(changes=changes, vars=result_vars)

    def decode(self, vars: Dict[str, str]) -> Base64Result:
        """Base64-decode selected variable values."""
        result_vars = dict(vars)
        changes: List[Base64Change] = []
        for key, value in vars.items():
            if not self._should_process(key):
                continue
            try:
                decoded = base64.b64decode(value.encode()).decode()
                result_vars[key] = decoded
                changes.append(Base64Change(key=key, original=value, result=decoded, operation="decode"))
            except Exception as exc:
                changes.append(Base64Change(key=key, original=value, result=value,
                                            operation="decode", error=str(exc)))
        return Base64Result(changes=changes, vars=result_vars)
