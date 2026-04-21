from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class WrapChange:
    key: str
    original: str
    wrapped: str

    def __repr__(self) -> str:
        return f"WrapChange(key={self.key!r}, len={len(self.wrapped)})"


@dataclass
class WrapResult:
    changes: List[WrapChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"WrapResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvWrapper:
    """Wraps env variable values at a specified column width."""

    def __init__(self, width: int = 80, continuation: str = "\\", skip_keys: Optional[List[str]] = None):
        if width < 1:
            raise ValueError("width must be at least 1")
        self.width = width
        self.continuation = continuation
        self.skip_keys = set(skip_keys or [])

    def wrap(self, vars: Dict[str, str]) -> WrapResult:
        changes: List[WrapChange] = []
        skipped: List[str] = []

        for key, value in vars.items():
            if key in self.skip_keys:
                skipped.append(key)
                continue

            if len(value) <= self.width:
                continue

            wrapped = self._wrap_value(value)
            if wrapped != value:
                changes.append(WrapChange(key=key, original=value, wrapped=wrapped))

        return WrapResult(changes=changes, skipped=skipped)

    def apply(self, vars: Dict[str, str]) -> Dict[str, str]:
        result = dict(vars)
        wrap_result = self.wrap(vars)
        for change in wrap_result.changes:
            result[change.key] = change.wrapped
        return result

    def _wrap_value(self, value: str) -> str:
        if len(value) <= self.width:
            return value
        lines = []
        while len(value) > self.width:
            lines.append(value[: self.width])
            value = value[self.width :]
        if value:
            lines.append(value)
        return (self.continuation + "\n").join(lines)
