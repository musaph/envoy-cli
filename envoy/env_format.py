"""Formatting and normalization of .env file variables."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FormatChange:
    key: str
    original: str
    formatted: str
    reason: str

    def __repr__(self) -> str:
        return f"FormatChange(key={self.key!r}, reason={self.reason!r})"


@dataclass
class FormatResult:
    vars: Dict[str, str]
    changes: List[FormatChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def __repr__(self) -> str:
        return (
            f"FormatResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvFormatter:
    """Normalizes and formats environment variable key/value pairs."""

    def __init__(
        self,
        uppercase_keys: bool = True,
        strip_values: bool = True,
        quote_values: bool = False,
        remove_empty: bool = False,
    ) -> None:
        self.uppercase_keys = uppercase_keys
        self.strip_values = strip_values
        self.quote_values = quote_values
        self.remove_empty = remove_empty

    def format(self, vars: Dict[str, str]) -> FormatResult:
        result_vars: Dict[str, str] = {}
        changes: List[FormatChange] = []
        skipped: List[str] = []

        for key, value in vars.items():
            original_key = key
            original_value = value

            if self.remove_empty and value.strip() == "":
                skipped.append(key)
                continue

            new_key = key.upper() if self.uppercase_keys else key
            new_value = value.strip() if self.strip_values else value

            if self.quote_values and not (
                new_value.startswith('"') and new_value.endswith('"')
            ):
                new_value = f'"{new_value}"'

            if new_key != original_key:
                changes.append(
                    FormatChange(original_key, original_key, new_key, "key uppercased")
                )
            if new_value != original_value:
                changes.append(
                    FormatChange(new_key, original_value, new_value, "value normalized")
                )

            result_vars[new_key] = new_value

        return FormatResult(vars=result_vars, changes=changes, skipped=skipped)
