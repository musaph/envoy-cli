"""Schema validation for .env files — enforce required keys, types, and patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SchemaField:
    key: str
    required: bool = True
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    description: str = ""

    def validate(self, value: Optional[str]) -> List[str]:
        """Return a list of error messages for this field."""
        errors: List[str] = []
        if value is None:
            if self.required:
                errors.append(f"{self.key}: required key is missing")
            return errors
        if self.pattern and not re.fullmatch(self.pattern, value):
            errors.append(
                f"{self.key}: value {value!r} does not match pattern {self.pattern!r}"
            )
        if self.allowed_values is not None and value not in self.allowed_values:
            errors.append(
                f"{self.key}: value {value!r} not in allowed values {self.allowed_values}"
            )
        return errors


@dataclass
class SchemaResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:  # pragma: no cover
        return f"SchemaResult(valid={self.is_valid}, errors={len(self.errors)}, warnings={len(self.warnings)})"


class EnvSchema:
    """Validates a dict of env vars against a list of SchemaField definitions."""

    def __init__(self, fields: List[SchemaField]) -> None:
        self._fields: Dict[str, SchemaField] = {f.key: f for f in fields}

    @classmethod
    def from_dict(cls, raw: Dict) -> "EnvSchema":
        """Build a schema from a plain dict (e.g. loaded from JSON/YAML config)."""
        fields = []
        for key, spec in raw.items():
            fields.append(
                SchemaField(
                    key=key,
                    required=spec.get("required", True),
                    pattern=spec.get("pattern"),
                    allowed_values=spec.get("allowed_values"),
                    description=spec.get("description", ""),
                )
            )
        return cls(fields)

    def validate(self, vars_: Dict[str, str]) -> SchemaResult:
        result = SchemaResult()
        for key, schema_field in self._fields.items():
            value = vars_.get(key)
            result.errors.extend(schema_field.validate(value))
        extra_keys = set(vars_) - set(self._fields)
        for key in sorted(extra_keys):
            result.warnings.append(f"{key}: key not defined in schema")
        return result
