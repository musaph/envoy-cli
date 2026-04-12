"""Manage default values for environment variables."""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DefaultEntry:
    key: str
    default_value: str
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "default_value": self.default_value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DefaultEntry":
        return cls(
            key=data["key"],
            default_value=data["default_value"],
            description=data.get("description", ""),
        )

    def __repr__(self) -> str:
        return f"DefaultEntry(key={self.key!r}, default={self.default_value!r})"


@dataclass
class DefaultsResult:
    applied: Dict[str, str] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)

    @property
    def has_applied(self) -> bool:
        return bool(self.applied)

    def __repr__(self) -> str:
        return (
            f"DefaultsResult(applied={len(self.applied)}, skipped={len(self.skipped)})"
        )


class EnvDefaultsManager:
    """Apply default values to env vars that are missing or empty."""

    def __init__(self, defaults: Dict[str, str], overwrite_empty: bool = True):
        self._defaults = defaults
        self._overwrite_empty = overwrite_empty

    def apply(self, vars: Dict[str, str]) -> DefaultsResult:
        """Return a new dict with defaults applied; report what changed."""
        result_vars = dict(vars)
        applied: Dict[str, str] = {}
        skipped: Dict[str, str] = {}

        for key, default_val in self._defaults.items():
            existing = result_vars.get(key)
            if existing is None:
                result_vars[key] = default_val
                applied[key] = default_val
            elif existing == "" and self._overwrite_empty:
                result_vars[key] = default_val
                applied[key] = default_val
            else:
                skipped[key] = existing

        return DefaultsResult(applied=applied, skipped=skipped)

    def missing_keys(
        self, vars: Dict[str, str], required: Optional[list] = None
    ) -> list:
        """Return keys from required (or all defaults) absent in vars."""
        keys = required if required is not None else list(self._defaults.keys())
        return [k for k in keys if k not in vars or vars[k] == ""]
