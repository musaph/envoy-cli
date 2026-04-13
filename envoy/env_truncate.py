"""Truncate long env var values to a maximum length."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TruncateChange:
    key: str
    original: str
    truncated: str
    original_len: int
    truncated_len: int

    def __repr__(self) -> str:
        return (
            f"TruncateChange(key={self.key!r}, "
            f"original_len={self.original_len}, "
            f"truncated_len={self.truncated_len})"
        )


@dataclass
class TruncateResult:
    changes: List[TruncateChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def __repr__(self) -> str:
        return (
            f"TruncateResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvTruncator:
    def __init__(self, max_length: int = 64, suffix: str = "...", skip_keys: Optional[List[str]] = None):
        if max_length < 1:
            raise ValueError("max_length must be at least 1")
        self.max_length = max_length
        self.suffix = suffix
        self.skip_keys = set(skip_keys or [])

    def truncate(self, vars: Dict[str, str]) -> TruncateResult:
        result = TruncateResult()
        for key, value in vars.items():
            if key in self.skip_keys:
                result.skipped.append(key)
                continue
            if len(value) > self.max_length:
                cut = self.max_length - len(self.suffix)
                cut = max(cut, 0)
                new_value = value[:cut] + self.suffix
                result.changes.append(TruncateChange(
                    key=key,
                    original=value,
                    truncated=new_value,
                    original_len=len(value),
                    truncated_len=len(new_value),
                ))
        return result

    def apply(self, vars: Dict[str, str]) -> Dict[str, str]:
        result = self.truncate(vars)
        out = dict(vars)
        for change in result.changes:
            out[change.key] = change.truncated
        return out
