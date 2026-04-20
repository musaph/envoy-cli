"""Lowercase key transformation for .env files.

Converts variable keys to lowercase, with optional conflict detection
when two keys would collide after lowercasing (e.g. DB_HOST and db_host).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LowercaseKeyChange:
    """Represents a single key lowercasing operation."""

    original_key: str
    new_key: str
    value: str
    was_overwritten: bool = False

    def __repr__(self) -> str:
        tag = " [overwritten]" if self.was_overwritten else ""
        return f"LowercaseKeyChange({self.original_key!r} -> {self.new_key!r}{tag})"


@dataclass
class LowercaseKeyResult:
    """Result of a lowercase-key transformation pass."""

    changes: List[LowercaseKeyChange] = field(default_factory=list)
    collisions: List[str] = field(default_factory=list)  # lowercased keys that collided
    output: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    @property
    def has_collisions(self) -> bool:
        return bool(self.collisions)

    @property
    def changed_keys(self) -> List[str]:
        return [c.original_key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"LowercaseKeyResult(changes={len(self.changes)}, "
            f"collisions={len(self.collisions)})"
        )


class EnvLowercaseKeyConverter:
    """Converts all keys in an env var dict to lowercase.

    When two keys map to the same lowercase form (a collision), the
    behaviour is controlled by ``overwrite``:

    - ``overwrite=True``  – last key wins (dict insertion order).
    - ``overwrite=False`` – first key wins; subsequent collisions are
      recorded in ``LowercaseKeyResult.collisions`` and skipped.
    """

    def __init__(self, overwrite: bool = False) -> None:
        self.overwrite = overwrite

    def convert(self, vars: Dict[str, str]) -> LowercaseKeyResult:
        """Return a new dict with all keys lowercased.

        Args:
            vars: Original mapping of env variable names to values.

        Returns:
            A :class:`LowercaseKeyResult` containing the transformed
            output, individual change records, and any collision keys.
        """
        output: Dict[str, str] = {}
        changes: List[LowercaseKeyChange] = []
        collisions: List[str] = []
        seen: Dict[str, str] = {}  # lowercase_key -> original_key that claimed it

        for original_key, value in vars.items():
            lower_key = original_key.lower()

            if lower_key in seen:
                # Collision detected
                if lower_key not in collisions:
                    collisions.append(lower_key)

                if self.overwrite:
                    # Replace the existing entry
                    changes.append(
                        LowercaseKeyChange(
                            original_key=original_key,
                            new_key=lower_key,
                            value=value,
                            was_overwritten=True,
                        )
                    )
                    output[lower_key] = value
                    seen[lower_key] = original_key
                # else: skip – first key wins, nothing added
            else:
                # No collision
                if original_key != lower_key:
                    changes.append(
                        LowercaseKeyChange(
                            original_key=original_key,
                            new_key=lower_key,
                            value=value,
                        )
                    )
                output[lower_key] = value
                seen[lower_key] = original_key

        return LowercaseKeyResult(
            changes=changes,
            collisions=collisions,
            output=output,
        )
