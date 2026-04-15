"""Pad env var values to a minimum length with a fill character."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PadChange:
    key: str
    original: str
    padded: str
    fill_char: str

    def __repr__(self) -> str:
        return f"PadChange(key={self.key!r}, original={self.original!r}, padded={self.padded!r})"


@dataclass
class PadResult:
    changes: List[PadChange] = field(default_factory=list)
    vars: Dict[str, str] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def changed_keys(self) -> List[str]:
        return [c.key for c in self.changes]

    def __repr__(self) -> str:
        return f"PadResult(changes={len(self.changes)}, vars={len(self.vars)})"


class EnvPadder:
    """Pads env var values to a minimum length."""

    def __init__(
        self,
        min_length: int = 8,
        fill_char: str = "0",
        align: str = "right",
        keys: Optional[List[str]] = None,
    ) -> None:
        if len(fill_char) != 1:
            raise ValueError("fill_char must be exactly one character")
        if align not in ("left", "right"):
            raise ValueError("align must be 'left' or 'right'")
        self.min_length = min_length
        self.fill_char = fill_char
        self.align = align
        self.keys = keys  # None means apply to all keys

    def pad(self, vars: Dict[str, str]) -> PadResult:
        result_vars: Dict[str, str] = {}
        changes: List[PadChange] = []

        for key, value in vars.items():
            if self.keys is not None and key not in self.keys:
                result_vars[key] = value
                continue

            if len(value) < self.min_length:
                if self.align == "right":
                    padded = value.rjust(self.min_length, self.fill_char)
                else:
                    padded = value.ljust(self.min_length, self.fill_char)
                changes.append(PadChange(key=key, original=value, padded=padded, fill_char=self.fill_char))
                result_vars[key] = padded
            else:
                result_vars[key] = value

        return PadResult(changes=changes, vars=result_vars)
