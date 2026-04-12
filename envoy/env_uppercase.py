"""Normalize environment variable keys to uppercase."""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class UppercaseChange:
    original: str
    normalized: str

    def __repr__(self) -> str:
        return f"UppercaseChange({self.original!r} -> {self.normalized!r})"


@dataclass
class UppercaseResult:
    vars: Dict[str, str] = field(default_factory=dict)
    changes: List[UppercaseChange] = field(default_factory=list)
    conflicts: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def __repr__(self) -> str:
        return (
            f"UppercaseResult(changes={len(self.changes)}, "
            f"conflicts={len(self.conflicts)})"
        )


class EnvUppercaser:
    """Normalizes all env var keys to uppercase, detecting key collisions."""

    def normalize(self, vars: Dict[str, str]) -> UppercaseResult:
        """Return a new dict with all keys uppercased.

        If two keys would collide after uppercasing (e.g. 'db_host' and
        'DB_HOST'), the conflict is recorded and the last-seen value wins.
        """
        result = UppercaseResult()
        seen: Dict[str, str] = {}  # uppercase_key -> original_key

        for key, value in vars.items():
            upper = key.upper()

            if upper in seen and seen[upper] != key:
                result.conflicts.append((seen[upper], key))

            if upper != key:
                result.changes.append(UppercaseChange(original=key, normalized=upper))

            seen[upper] = key
            result.vars[upper] = value

        return result
