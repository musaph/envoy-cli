from dataclasses import dataclass, field
from typing import Dict, List, Optional
import hashlib
import base64


@dataclass
class ObfuscateChange:
    key: str
    original: str
    obfuscated: str
    method: str

    def __repr__(self) -> str:
        return f"ObfuscateChange(key={self.key!r}, method={self.method!r})"


@dataclass
class ObfuscateResult:
    vars: Dict[str, str] = field(default_factory=dict)
    changes: List[ObfuscateChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def __repr__(self) -> str:
        return (
            f"ObfuscateResult(changed={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvObfuscator:
    """Obfuscates env var values using hash or base64 encoding."""

    METHODS = ("hash", "base64")

    def __init__(
        self,
        keys: Optional[List[str]] = None,
        method: str = "hash",
        hash_length: int = 12,
    ) -> None:
        if method not in self.METHODS:
            raise ValueError(f"method must be one of {self.METHODS}")
        self._keys = set(keys) if keys else None
        self._method = method
        self._hash_length = hash_length

    def _obfuscate(self, value: str) -> str:
        if self._method == "hash":
            digest = hashlib.sha256(value.encode()).hexdigest()
            return digest[: self._hash_length]
        encoded = base64.b64encode(value.encode()).decode()
        return encoded

    def obfuscate(self, vars: Dict[str, str]) -> ObfuscateResult:
        result_vars: Dict[str, str] = {}
        changes: List[ObfuscateChange] = []
        skipped: List[str] = []

        for key, value in vars.items():
            if self._keys is not None and key not in self._keys:
                result_vars[key] = value
                skipped.append(key)
                continue
            obfuscated = self._obfuscate(value)
            result_vars[key] = obfuscated
            changes.append(
                ObfuscateChange(
                    key=key,
                    original=value,
                    obfuscated=obfuscated,
                    method=self._method,
                )
            )

        return ObfuscateResult(vars=result_vars, changes=changes, skipped=skipped)
