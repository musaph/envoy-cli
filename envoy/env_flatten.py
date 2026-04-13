"""Flatten nested env var structures (e.g. JSON-valued vars) into dot-notation keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json


@dataclass
class FlattenChange:
    original_key: str
    derived_key: str
    value: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"FlattenChange({self.original_key!r} -> {self.derived_key!r}={self.value!r})"


@dataclass
class FlattenResult:
    flattened: Dict[str, str] = field(default_factory=dict)
    changes: List[FlattenChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FlattenResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvFlattener:
    """Expand JSON-valued environment variables into dot-notation keys."""

    def __init__(self, separator: str = ".", prefix_original: bool = False) -> None:
        self._sep = separator
        self._prefix_original = prefix_original

    def flatten(self, vars: Dict[str, str]) -> FlattenResult:
        result = FlattenResult()
        for key, value in vars.items():
            parsed = self._try_parse_json(value)
            if parsed is None or not isinstance(parsed, dict):
                result.flattened[key] = value
                result.skipped.append(key)
                continue
            for derived_key, leaf_value in self._walk(key, parsed):
                str_value = str(leaf_value) if not isinstance(leaf_value, str) else leaf_value
                result.flattened[derived_key] = str_value
                result.changes.append(FlattenChange(key, derived_key, str_value))
        return result

    def _walk(self, prefix: str, obj: Any):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from self._walk(f"{prefix}{self._sep}{k}", v)
        else:
            yield prefix, obj

    @staticmethod
    def _try_parse_json(value: str) -> Optional[Any]:
        stripped = value.strip()
        if stripped.startswith("{"):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return None
        return None
