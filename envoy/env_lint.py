"""Lint rules for .env files — checks for common issues and best practices."""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class LintIssue:
    key: str
    message: str
    severity: str  # 'error' | 'warning' | 'info'

    def __repr__(self) -> str:
        return f"LintIssue({self.severity}, {self.key!r}: {self.message})"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:
        return f"LintResult(errors={len(self.errors)}, warnings={len(self.warnings)})"


class EnvLinter:
    """Runs a series of lint checks against a dict of env vars."""

    MAX_KEY_LENGTH = 64
    MAX_VALUE_LENGTH = 512

    def lint(self, vars: Dict[str, str]) -> LintResult:
        result = LintResult()
        for key, value in vars.items():
            result.issues.extend(self._check_key(key))
            result.issues.extend(self._check_value(key, value))
        result.issues.extend(self._check_duplicates(vars))
        return result

    def _check_key(self, key: str) -> List[LintIssue]:
        issues = []
        if not key:
            issues.append(LintIssue(key="", message="Empty key found.", severity="error"))
            return issues
        if not key[0].isalpha() and key[0] != "_":
            issues.append(LintIssue(key=key, message="Key must start with a letter or underscore.", severity="error"))
        if not all(c.isalnum() or c == "_" for c in key):
            issues.append(LintIssue(key=key, message="Key contains invalid characters (only A-Z, 0-9, _ allowed).", severity="error"))
        if key != key.upper():
            issues.append(LintIssue(key=key, message="Key is not uppercase.", severity="warning"))
        if len(key) > self.MAX_KEY_LENGTH:
            issues.append(LintIssue(key=key, message=f"Key exceeds {self.MAX_KEY_LENGTH} characters.", severity="warning"))
        return issues

    def _check_value(self, key: str, value: str) -> List[LintIssue]:
        issues = []
        if value == "":
            issues.append(LintIssue(key=key, message="Value is empty.", severity="info"))
        if len(value) > self.MAX_VALUE_LENGTH:
            issues.append(LintIssue(key=key, message=f"Value exceeds {self.MAX_VALUE_LENGTH} characters.", severity="warning"))
        if value != value.strip():
            issues.append(LintIssue(key=key, message="Value has leading or trailing whitespace.", severity="warning"))
        return issues

    def _check_duplicates(self, vars: Dict[str, str]) -> List[LintIssue]:
        seen: Dict[str, int] = {}
        for key in vars:
            seen[key] = seen.get(key, 0) + 1
        return [
            LintIssue(key=k, message="Duplicate key detected.", severity="error")
            for k, count in seen.items() if count > 1
        ]
