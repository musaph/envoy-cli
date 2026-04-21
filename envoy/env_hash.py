"""env_hash.py — Hash values of env variables using configurable algorithms."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class HashChange:
    key: str
    original: str
    hashed: str
    algorithm: str

    def __repr__(self) -> str:
        return f"HashChange(key={self.key!r}, algorithm={self.algorithm!r})"


@dataclass
class HashResult:
    changes: List[HashChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"HashResult(changed={len(self.changes)}, skipped={len(self.skipped)})"
        )


SUPPORTED_ALGORITHMS = {"md5", "sha1", "sha256", "sha512"}


class EnvHasher:
    """Hash env variable values using a configurable algorithm."""

    def __init__(
        self,
        algorithm: str = "sha256",
        keys: Optional[List[str]] = None,
        prefix: str = "",
    ) -> None:
        if algorithm not in SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported algorithm {algorithm!r}. "
                f"Choose from: {sorted(SUPPORTED_ALGORITHMS)}"
            )
        self.algorithm = algorithm
        self.keys = set(keys) if keys else None
        self.prefix = prefix

    def _hash(self, value: str) -> str:
        h = hashlib.new(self.algorithm)
        h.update(value.encode("utf-8"))
        digest = h.hexdigest()
        return f"{self.prefix}{digest}" if self.prefix else digest

    def hash_vars(
        self, vars_: Dict[str, str]
    ) -> HashResult:
        changes: List[HashChange] = []
        skipped: List[str] = []

        for key, value in vars_.items():
            if self.keys is not None and key not in self.keys:
                skipped.append(key)
                continue
            hashed = self._hash(value)
            changes.append(
                HashChange(
                    key=key,
                    original=value,
                    hashed=hashed,
                    algorithm=self.algorithm,
                )
            )

        return HashResult(changes=changes, skipped=skipped)

    def apply(self, vars_: Dict[str, str]) -> Dict[str, str]:
        result = self.hash_vars(vars_)
        out = dict(vars_)
        for change in result.changes:
            out[change.key] = change.hashed
        return out
