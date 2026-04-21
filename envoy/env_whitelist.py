from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class WhitelistViolation:
    key: str
    reason: str

    def __repr__(self) -> str:
        return f"WhitelistViolation(key={self.key!r}, reason={self.reason!r})"


@dataclass
class WhitelistResult:
    allowed: Dict[str, str] = field(default_factory=dict)
    violations: List[WhitelistViolation] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.violations) == 0

    def __repr__(self) -> str:
        return (
            f"WhitelistResult(allowed={len(self.allowed)}, "
            f"violations={len(self.violations)})"
        )


class EnvWhitelist:
    """Filters env vars to only those present in an allowed-keys list."""

    def __init__(self, allowed_keys: List[str], strict: bool = True):
        self._allowed = set(allowed_keys)
        self._strict = strict

    def check(self, vars: Dict[str, str]) -> WhitelistResult:
        """Return allowed vars and flag any keys not in the whitelist."""
        allowed: Dict[str, str] = {}
        violations: List[WhitelistViolation] = []

        for key, value in vars.items():
            if key in self._allowed:
                allowed[key] = value
            else:
                violations.append(
                    WhitelistViolation(key=key, reason="key not in whitelist")
                )

        return WhitelistResult(allowed=allowed, violations=violations)

    def filter(self, vars: Dict[str, str]) -> Dict[str, str]:
        """Return only the vars whose keys are in the whitelist."""
        return {k: v for k, v in vars.items() if k in self._allowed}

    def add_key(self, key: str) -> None:
        """Add a single key to the whitelist at runtime."""
        self._allowed.add(key)

    def remove_key(self, key: str) -> None:
        """Remove a key from the whitelist, raising KeyError if not present."""
        if key not in self._allowed:
            raise KeyError(f"Key {key!r} is not in the whitelist")
        self._allowed.discard(key)

    @property
    def allowed_keys(self) -> List[str]:
        return sorted(self._allowed)
