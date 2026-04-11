"""Trim whitespace and normalize values in .env variable sets."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TrimResult:
    trimmed: Dict[str, str] = field(default_factory=dict)
    changed_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"TrimResult(changed={len(self.changed_keys)}, "
            f"skipped={len(self.skipped_keys)}, "
            f"total={len(self.trimmed)})"
        )

    @property
    def has_changes(self) -> bool:
        return len(self.changed_keys) > 0


class EnvTrimmer:
    """Trims and normalizes whitespace in environment variable values."""

    def __init__(
        self,
        strip_quotes: bool = False,
        normalize_empty: bool = False,
        skip_keys: Optional[List[str]] = None,
    ) -> None:
        self.strip_quotes = strip_quotes
        self.normalize_empty = normalize_empty
        self.skip_keys: List[str] = skip_keys or []

    def trim(self, vars: Dict[str, str]) -> TrimResult:
        """Return a TrimResult with whitespace-trimmed values."""
        trimmed: Dict[str, str] = {}
        changed_keys: List[str] = []
        skipped_keys: List[str] = []

        for key, value in vars.items():
            if key in self.skip_keys:
                trimmed[key] = value
                skipped_keys.append(key)
                continue

            new_value = value.strip()

            if self.strip_quotes:
                new_value = self._strip_surrounding_quotes(new_value)

            if self.normalize_empty and new_value == "":
                new_value = ""

            trimmed[key] = new_value
            if new_value != value:
                changed_keys.append(key)

        return TrimResult(
            trimmed=trimmed,
            changed_keys=changed_keys,
            skipped_keys=skipped_keys,
        )

    @staticmethod
    def _strip_surrounding_quotes(value: str) -> str:
        """Remove a single layer of matching surrounding quotes."""
        if len(value) >= 2:
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                return value[1:-1]
        return value
