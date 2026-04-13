"""Pivot env vars by swapping keys and values, with collision detection."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PivotChange:
    original_key: str
    original_value: str
    new_key: str
    new_value: str

    def __repr__(self) -> str:
        return f"PivotChange({self.original_key!r} -> {self.new_key!r})"


@dataclass
class PivotResult:
    pivoted: Dict[str, str] = field(default_factory=dict)
    changes: List[PivotChange] = field(default_factory=list)
    collisions: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    @property
    def has_collisions(self) -> bool:
        return bool(self.collisions)

    def __repr__(self) -> str:
        return (
            f"PivotResult(changes={len(self.changes)}, "
            f"collisions={len(self.collisions)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvPivoter:
    """Swaps keys and values in an env var dict."""

    def __init__(self, skip_empty: bool = True, on_collision: str = "skip") -> None:
        """Args:
            skip_empty: Skip vars with empty values (can't become keys).
            on_collision: 'skip' or 'overwrite' when new keys collide.
        """
        self.skip_empty = skip_empty
        self.on_collision = on_collision

    def pivot(self, vars: Dict[str, str]) -> PivotResult:
        result = PivotResult()
        seen_new_keys: Dict[str, str] = {}

        for key, value in vars.items():
            if self.skip_empty and not value:
                result.skipped.append(key)
                continue

            new_key = value
            new_value = key

            if new_key in seen_new_keys:
                result.collisions.append(new_key)
                if self.on_collision == "skip":
                    continue

            seen_new_keys[new_key] = new_value
            result.pivoted[new_key] = new_value
            result.changes.append(
                PivotChange(
                    original_key=key,
                    original_value=value,
                    new_key=new_key,
                    new_value=new_value,
                )
            )

        return result
