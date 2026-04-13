from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class SanitizeChange:
    key: str
    original: str
    sanitized: str
    reason: str

    def __repr__(self) -> str:
        return f"SanitizeChange(key={self.key!r}, reason={self.reason!r})"


@dataclass
class SanitizeResult:
    changes: List[SanitizeChange] = field(default_factory=list)
    sanitized: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def __repr__(self) -> str:
        return f"SanitizeResult(changes={len(self.changes)}, has_changes={self.has_changes})"


class EnvSanitizer:
    """Sanitizes env var values by stripping unsafe characters and patterns."""

    # Patterns considered unsafe in env values
    _CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    _NULL_BYTE_RE = re.compile(r"\x00")

    def __init__(
        self,
        strip_whitespace: bool = True,
        remove_control_chars: bool = True,
        max_length: Optional[int] = None,
    ) -> None:
        self.strip_whitespace = strip_whitespace
        self.remove_control_chars = remove_control_chars
        self.max_length = max_length

    def sanitize(self, vars: Dict[str, str]) -> SanitizeResult:
        result = SanitizeResult()
        for key, value in vars.items():
            sanitized, reasons = self._sanitize_value(value)
            result.sanitized[key] = sanitized
            if sanitized != value:
                result.changes.append(
                    SanitizeChange(
                        key=key,
                        original=value,
                        sanitized=sanitized,
                        reason="; ".join(reasons),
                    )
                )
        return result

    def _sanitize_value(self, value: str):
        reasons = []
        result = value

        if self.remove_control_chars:
            cleaned = self._CONTROL_CHARS_RE.sub("", result)
            if cleaned != result:
                reasons.append("removed control characters")
                result = cleaned

        if self.strip_whitespace:
            stripped = result.strip()
            if stripped != result:
                reasons.append("stripped surrounding whitespace")
                result = stripped

        if self.max_length is not None and len(result) > self.max_length:
            result = result[: self.max_length]
            reasons.append(f"truncated to {self.max_length} characters")

        return result, reasons
