"""Redaction utilities for masking sensitive values in .env output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.secrets import SecretScanner

DEFAULT_MASK = "***"
PARTIAL_MASK_VISIBLE = 4  # characters to keep at end for partial masking


@dataclass
class RedactedVar:
    key: str
    original_value: str
    redacted_value: str
    was_redacted: bool

    def __repr__(self) -> str:
        status = "REDACTED" if self.was_redacted else "plain"
        return f"RedactedVar({self.key!r}, {status})"


class EnvRedactor:
    """Masks sensitive variable values before display or logging."""

    def __init__(
        self,
        scanner: Optional[SecretScanner] = None,
        mask: str = DEFAULT_MASK,
        partial: bool = False,
    ) -> None:
        self._scanner = scanner or SecretScanner()
        self._mask = mask
        self._partial = partial

    def _mask_value(self, value: str) -> str:
        if not value:
            return self._mask
        if self._partial and len(value) > PARTIAL_MASK_VISIBLE:
            return self._mask + value[-PARTIAL_MASK_VISIBLE:]
        return self._mask

    def redact(self, vars: Dict[str, str]) -> List[RedactedVar]:
        """Return a list of RedactedVar for each entry in vars."""
        results: List[RedactedVar] = []
        for key, value in vars.items():
            sensitive = self._scanner.is_sensitive_key(key)
            redacted_value = self._mask_value(value) if sensitive else value
            results.append(
                RedactedVar(
                    key=key,
                    original_value=value,
                    redacted_value=redacted_value,
                    was_redacted=sensitive,
                )
            )
        return results

    def redact_dict(self, vars: Dict[str, str]) -> Dict[str, str]:
        """Return a new dict with sensitive values replaced by the mask."""
        return {
            rv.key: rv.redacted_value for rv in self.redact(vars)
        }

    def summary(self, vars: Dict[str, str]) -> str:
        """Human-readable summary of how many keys were redacted."""
        results = self.redact(vars)
        total = len(results)
        redacted = sum(1 for r in results if r.was_redacted)
        return f"{redacted}/{total} variable(s) redacted."
