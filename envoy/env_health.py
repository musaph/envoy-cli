"""Health check module for .env files — detects missing, empty, and duplicate keys."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class HealthIssue:
    level: str  # 'error' | 'warning' | 'info'
    key: Optional[str]
    message: str

    def __repr__(self) -> str:
        key_part = f"[{self.key}] " if self.key else ""
        return f"HealthIssue({self.level}: {key_part}{self.message})"


@dataclass
class HealthReport:
    issues: List[HealthIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[HealthIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> List[HealthIssue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def is_healthy(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        return (
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s) — "
            f"{'healthy' if self.is_healthy else 'unhealthy'}"
        )


class EnvHealthChecker:
    """Runs health checks against a parsed env variable dict."""

    def __init__(self, required_keys: Optional[List[str]] = None) -> None:
        self.required_keys: List[str] = required_keys or []

    def check(self, vars: Dict[str, str]) -> HealthReport:
        report = HealthReport()
        seen: Dict[str, int] = {}

        for key, value in vars.items():
            # Track for duplicate detection (parser normally deduplicates,
            # but raw sources may not)
            seen[key] = seen.get(key, 0) + 1

            if value.strip() == "":
                report.issues.append(
                    HealthIssue(level="warning", key=key, message="Value is empty")
                )

        for key, count in seen.items():
            if count > 1:
                report.issues.append(
                    HealthIssue(
                        level="error",
                        key=key,
                        message=f"Duplicate key appears {count} times",
                    )
                )

        for req in self.required_keys:
            if req not in vars:
                report.issues.append(
                    HealthIssue(
                        level="error",
                        key=req,
                        message="Required key is missing",
                    )
                )

        return report
