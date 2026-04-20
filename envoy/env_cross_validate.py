"""Cross-validation of env variables against an external reference set.

Allows users to verify that a local .env file contains all keys defined
in a reference env (e.g. .env.example), and optionally that no extra
undeclared keys are present.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class CrossValidationViolation:
    """Represents a single cross-validation violation."""

    key: str
    reason: str  # 'missing' | 'undeclared'

    def __repr__(self) -> str:
        return f"CrossValidationViolation(key={self.key!r}, reason={self.reason!r})"


@dataclass
class CrossValidationResult:
    """Holds the outcome of a cross-validation run."""

    violations: List[CrossValidationViolation] = field(default_factory=list)
    checked_keys: int = 0
    reference_keys: int = 0

    @property
    def is_valid(self) -> bool:
        """True when no violations were found."""
        return len(self.violations) == 0

    @property
    def missing(self) -> List[CrossValidationViolation]:
        """Keys present in the reference but absent from the target."""
        return [v for v in self.violations if v.reason == "missing"]

    @property
    def undeclared(self) -> List[CrossValidationViolation]:
        """Keys present in the target but absent from the reference."""
        return [v for v in self.violations if v.reason == "undeclared"]

    def __repr__(self) -> str:
        return (
            f"CrossValidationResult("
            f"valid={self.is_valid}, "
            f"missing={len(self.missing)}, "
            f"undeclared={len(self.undeclared)}, "
            f"checked={self.checked_keys})"
        )


class EnvCrossValidator:
    """Validates a target env dict against a reference env dict.

    Args:
        strict: When True, keys in the target that are not in the
                reference are reported as 'undeclared' violations.
    """

    def __init__(self, strict: bool = False) -> None:
        self.strict = strict

    def validate(
        self,
        target: Dict[str, str],
        reference: Dict[str, str],
        ignore_keys: Optional[List[str]] = None,
    ) -> CrossValidationResult:
        """Run cross-validation of *target* against *reference*.

        Args:
            target: The env vars to validate (e.g. loaded from .env).
            reference: The authoritative set of expected keys
                       (e.g. loaded from .env.example).
            ignore_keys: Keys to skip during validation on both sides.

        Returns:
            A :class:`CrossValidationResult` describing any violations.
        """
        skip: Set[str] = set(ignore_keys or [])
        ref_keys: Set[str] = {k for k in reference if k not in skip}
        tgt_keys: Set[str] = {k for k in target if k not in skip}

        violations: List[CrossValidationViolation] = []

        # Keys required by reference but missing from target
        for key in sorted(ref_keys - tgt_keys):
            violations.append(
                CrossValidationViolation(key=key, reason="missing")
            )

        # Keys in target not declared in reference (only in strict mode)
        if self.strict:
            for key in sorted(tgt_keys - ref_keys):
                violations.append(
                    CrossValidationViolation(key=key, reason="undeclared")
                )

        return CrossValidationResult(
            violations=violations,
            checked_keys=len(tgt_keys),
            reference_keys=len(ref_keys),
        )
