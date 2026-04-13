"""Compute and verify checksums for .env variable sets."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ChecksumResult:
    checksum: str
    algorithm: str = "sha256"
    key_count: int = 0
    mismatches: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ChecksumResult(algorithm={self.algorithm!r}, "
            f"key_count={self.key_count}, "
            f"mismatches={len(self.mismatches)})"
        )

    @property
    def is_valid(self) -> bool:
        return len(self.mismatches) == 0


class EnvChecksummer:
    """Compute and verify deterministic checksums over env var dicts."""

    SUPPORTED = ("sha256", "sha1", "md5")

    def __init__(self, algorithm: str = "sha256") -> None:
        if algorithm not in self.SUPPORTED:
            raise ValueError(
                f"Unsupported algorithm {algorithm!r}. Choose from {self.SUPPORTED}."
            )
        self.algorithm = algorithm

    def _digest(self, vars: Dict[str, str]) -> str:
        """Return a deterministic hex digest for *vars*."""
        canonical = json.dumps(
            {k: vars[k] for k in sorted(vars)}, separators=(",", ":")
        ).encode()
        h = hashlib.new(self.algorithm)
        h.update(canonical)
        return h.hexdigest()

    def compute(self, vars: Dict[str, str]) -> ChecksumResult:
        """Compute a checksum for *vars* and return a ChecksumResult."""
        digest = self._digest(vars)
        return ChecksumResult(
            checksum=digest,
            algorithm=self.algorithm,
            key_count=len(vars),
        )

    def verify(
        self, vars: Dict[str, str], expected: str
    ) -> ChecksumResult:
        """Verify *vars* against *expected* checksum.

        Returns a ChecksumResult whose ``is_valid`` flag indicates success.
        Keys that are missing or altered are listed in ``mismatches``.
        """
        actual = self._digest(vars)
        mismatches: List[str] = [] if actual == expected else ["<checksum mismatch>"]
        return ChecksumResult(
            checksum=actual,
            algorithm=self.algorithm,
            key_count=len(vars),
            mismatches=mismatches,
        )
