"""Validation utilities for .env file variables and values."""

import re
from dataclasses import dataclass, field
from typing import List, Optional


VALID_KEY_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
SECRET_KEY_HINTS = re.compile(
    r'(password|secret|token|key|api_key|private|auth|credential)',
    re.IGNORECASE,
)


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str  # 'error' | 'warning'

    def __repr__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == 'error']

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == 'warning']

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add(self, key: str, message: str, severity: str = 'error') -> None:
        self.issues.append(ValidationIssue(key=key, message=message, severity=severity))


class EnvValidator:
    """Validates parsed .env variable dictionaries."""

    def validate(self, variables: dict) -> ValidationResult:
        result = ValidationResult()

        if not variables:
            result.add('__file__', 'No variables found in env file.', severity='warning')
            return result

        for key, value in variables.items():
            self._validate_key(key, result)
            self._validate_value(key, value, result)

        return result

    def _validate_key(self, key: str, result: ValidationResult) -> None:
        if not key:
            result.add(key, 'Key must not be empty.')
            return
        if not VALID_KEY_PATTERN.match(key):
            result.add(
                key,
                f"Key '{key}' contains invalid characters. Use A-Z, a-z, 0-9, or underscore.",
            )
        if key != key.upper():
            result.add(
                key,
                f"Key '{key}' is not uppercase. Convention recommends uppercase keys.",
                severity='warning',
            )

    def _validate_value(
        self, key: str, value: Optional[str], result: ValidationResult
    ) -> None:
        if value is None or value == '':
            if SECRET_KEY_HINTS.search(key):
                result.add(
                    key,
                    f"Key '{key}' looks like a secret but has an empty value.",
                    severity='warning',
                )
