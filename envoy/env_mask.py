"""Masking module: selectively mask env var values for safe display."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.secrets import SecretScanner

_DEFAULT_MASK = "********"
_DEFAULT_REVEAL_CHARS = 0


@dataclass
class MaskResult:
    original: Dict[str, str]
    masked: Dict[str, str]
    masked_keys: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"MaskResult(total={len(self.original)}, "
            f"masked={len(self.masked_keys)})"
        )


class EnvMasker:
    """Mask sensitive env var values, optionally revealing a few trailing chars."""

    def __init__(
        self,
        scanner: Optional[SecretScanner] = None,
        mask: str = _DEFAULT_MASK,
        reveal_chars: int = _DEFAULT_REVEAL_CHARS,
    ) -> None:
        self._scanner = scanner or SecretScanner()
        self._mask = mask
        self._reveal_chars = max(0, reveal_chars)

    def _mask_value(self, value: str) -> str:
        if not value:
            return self._mask
        if self._reveal_chars and len(value) > self._reveal_chars:
            return self._mask + value[-self._reveal_chars :]
        return self._mask

    def mask(self, vars: Dict[str, str]) -> MaskResult:
        """Return a MaskResult with sensitive values replaced by the mask string."""
        masked: Dict[str, str] = {}
        masked_keys: List[str] = []
        for key, value in vars.items():
            if self._scanner.is_sensitive_key(key):
                masked[key] = self._mask_value(value)
                masked_keys.append(key)
            else:
                masked[key] = value
        return MaskResult(original=vars, masked=masked, masked_keys=masked_keys)

    def mask_single(self, key: str, value: str) -> str:
        """Mask a single value if its key is considered sensitive."""
        if self._scanner.is_sensitive_key(key):
            return self._mask_value(value)
        return value
