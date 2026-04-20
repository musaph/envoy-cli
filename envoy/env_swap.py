"""Swap keys and values in an env variable set."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SwapChange:
    original_key: str
    original_value: str
    new_key: str
    new_value: str

    def __repr__(self) -> str:
        return (
            f"SwapChange({self.original_key!r}={self.original_value!r} "
            f"-> {self.new_key!r}={self.new_value!r})"
        )


@dataclass
class SwapResult:
    changes: List[SwapChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    vars: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.original_key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"SwapResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)})"
        )


class EnvSwapper:
    """Swap keys and values: new_key=old_key, new_value=old_value."""

    def __init__(self, overwrite: bool = False) -> None:
        self.overwrite = overwrite

    def swap(self, vars: Dict[str, str]) -> SwapResult:
        """Return a new dict with keys and values swapped."""
        result = SwapResult()
        new_vars: Dict[str, str] = {}

        for key, value in vars.items():
            new_key = value
            new_value = key

            if not new_key:
                result.skipped.append(key)
                continue

            if new_key in new_vars and not self.overwrite:
                result.skipped.append(key)
                continue

            result.changes.append(
                SwapChange(
                    original_key=key,
                    original_value=value,
                    new_key=new_key,
                    new_value=new_value,
                )
            )
            new_vars[new_key] = new_value

        result.vars = new_vars
        return result
