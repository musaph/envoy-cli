"""Slugify environment variable keys: normalize to UPPER_SNAKE_CASE."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SlugifyChange:
    key: str
    original_key: str
    value: str

    def __repr__(self) -> str:
        return f"SlugifyChange(original={self.original_key!r}, slugified={self.key!r})"


@dataclass
class SlugifyResult:
    vars: Dict[str, str] = field(default_factory=dict)
    changes: List[SlugifyChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.original_key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"SlugifyResult(changed={len(self.changes)}, "
            f"skipped={len(self.skipped)}, total={len(self.vars)})"
        )


class EnvSlugifier:
    """Converts environment variable keys to UPPER_SNAKE_CASE slugs."""

    def __init__(self, overwrite: bool = False) -> None:
        self.overwrite = overwrite

    @staticmethod
    def _slugify(key: str) -> str:
        """Convert a key to UPPER_SNAKE_CASE."""
        # Insert underscore between camelCase transitions
        key = re.sub(r'([a-z])([A-Z])', r'\1_\2', key)
        # Replace any non-alphanumeric characters with underscores
        key = re.sub(r'[^A-Za-z0-9]+', '_', key)
        # Strip leading/trailing underscores
        key = key.strip('_')
        return key.upper()

    def slugify(self, vars: Dict[str, str]) -> SlugifyResult:
        result_vars: Dict[str, str] = {}
        changes: List[SlugifyChange] = []
        skipped: List[str] = []

        for original_key, value in vars.items():
            new_key = self._slugify(original_key)
            if new_key == original_key:
                result_vars[original_key] = value
                continue
            if new_key in result_vars or new_key in vars:
                if not self.overwrite:
                    skipped.append(original_key)
                    result_vars[original_key] = value
                    continue
            changes.append(SlugifyChange(key=new_key, original_key=original_key, value=value))
            result_vars[new_key] = value

        return SlugifyResult(vars=result_vars, changes=changes, skipped=skipped)
