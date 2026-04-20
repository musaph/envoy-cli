"""env_squash.py – collapse duplicate-prefixed keys into a single canonical key."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SquashChange:
    canonical: str
    absorbed: List[str]
    chosen_value: str

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SquashChange(canonical={self.canonical!r}, "
            f"absorbed={self.absorbed!r}, value={self.chosen_value!r})"
        )


@dataclass
class SquashResult:
    changes: List[SquashChange] = field(default_factory=list)
    output: Dict[str, str] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return bool(self.changes)

    def absorbed_keys(self) -> List[str]:
        result: List[str] = []
        for c in self.changes:
            result.extend(c.absorbed)
        return result

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SquashResult(changes={len(self.changes)}, "
            f"absorbed={len(self.absorbed_keys())})"
        )


class EnvSquasher:
    """Merge keys that share a common prefix alias into one canonical key.

    Args:
        alias_map: mapping of {canonical_key: [alias1, alias2, ...]}
        prefer_last: when True keep the *last* alias value found; otherwise
                     keep the *first* (canonical key value takes priority).
    """

    def __init__(
        self,
        alias_map: Optional[Dict[str, List[str]]] = None,
        prefer_last: bool = False,
    ) -> None:
        self._alias_map: Dict[str, List[str]] = alias_map or {}
        self._prefer_last = prefer_last

    def squash(self, vars: Dict[str, str]) -> SquashResult:
        output = dict(vars)
        changes: List[SquashChange] = []

        for canonical, aliases in self._alias_map.items():
            present_aliases = [a for a in aliases if a in output]
            if not present_aliases:
                continue

            candidates: List[str] = []
            if canonical in output:
                candidates.append(canonical)
            candidates.extend(present_aliases)

            chosen_value = candidates[-1 if self._prefer_last else 0]
            chosen_value = output[chosen_value]

            absorbed = [a for a in present_aliases]
            for a in absorbed:
                del output[a]
            output[canonical] = chosen_value

            changes.append(SquashChange(
                canonical=canonical,
                absorbed=absorbed,
                chosen_value=chosen_value,
            ))

        return SquashResult(changes=changes, output=output)
