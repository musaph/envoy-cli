"""Mask env var values matching configurable patterns or key rules."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class MaskPatternChange:
    key: str
    original: str
    masked: str

    def __repr__(self) -> str:
        return f"MaskPatternChange(key={self.key!r}, masked={self.masked!r})"


@dataclass
class MaskPatternResult:
    changes: List[MaskPatternChange] = field(default_factory=list)
    output: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return f"MaskPatternResult(changes={len(self.changes)}, has_changes={self.has_changes})"


class EnvMaskPattern:
    """Masks env var values whose keys match given patterns or whose values match a regex."""

    DEFAULT_KEY_PATTERNS = [
        re.compile(r"(password|secret|token|key|auth|credential|private)", re.IGNORECASE),
    ]
    MASK_CHAR = "*"
    MASK_LENGTH = 8

    def __init__(
        self,
        key_patterns: Optional[List[re.Pattern]] = None,
        value_pattern: Optional[re.Pattern] = None,
        reveal_chars: int = 0,
    ):
        self.key_patterns = key_patterns if key_patterns is not None else self.DEFAULT_KEY_PATTERNS
        self.value_pattern = value_pattern
        self.reveal_chars = reveal_chars

    def _should_mask(self, key: str, value: str) -> bool:
        for pat in self.key_patterns:
            if pat.search(key):
                return True
        if self.value_pattern and self.value_pattern.search(value):
            return True
        return False

    def _mask(self, value: str) -> str:
        if not value:
            return value
        if self.reveal_chars > 0 and len(value) > self.reveal_chars:
            return value[: self.reveal_chars] + self.MASK_CHAR * self.MASK_LENGTH
        return self.MASK_CHAR * self.MASK_LENGTH

    def apply(self, vars: Dict[str, str]) -> MaskPatternResult:
        output: Dict[str, str] = {}
        changes: List[MaskPatternChange] = []
        for key, value in vars.items():
            if self._should_mask(key, value):
                masked = self._mask(value)
                if masked != value:
                    changes.append(MaskPatternChange(key=key, original=value, masked=masked))
                output[key] = masked
            else:
                output[key] = value
        return MaskPatternResult(changes=changes, output=output)
