"""env_dotdiff.py — Compute a dot-notation diff between two env var dicts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DotDiffEntry:
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    status: str  # 'added' | 'removed' | 'changed' | 'unchanged'

    def __repr__(self) -> str:
        return f"DotDiffEntry(key={self.key!r}, status={self.status!r})"


@dataclass
class DotDiffResult:
    entries: List[DotDiffEntry] = field(default_factory=list)

    @property
    def added(self) -> List[DotDiffEntry]:
        return [e for e in self.entries if e.status == "added"]

    @property
    def removed(self) -> List[DotDiffEntry]:
        return [e for e in self.entries if e.status == "removed"]

    @property
    def changed(self) -> List[DotDiffEntry]:
        return [e for e in self.entries if e.status == "changed"]

    @property
    def unchanged(self) -> List[DotDiffEntry]:
        return [e for e in self.entries if e.status == "unchanged"]

    @property
    def has_diff(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def __repr__(self) -> str:
        return (
            f"DotDiffResult(added={len(self.added)}, removed={len(self.removed)}, "
            f"changed={len(self.changed)}, unchanged={len(self.unchanged)})"
        )


class EnvDotDiffer:
    """Compute a key-level diff between two env var dictionaries."""

    def __init__(self, ignore_case: bool = False) -> None:
        self.ignore_case = ignore_case

    def _normalise(self, value: str) -> str:
        return value.lower() if self.ignore_case else value

    def diff(
        self,
        old: Dict[str, str],
        new: Dict[str, str],
        include_unchanged: bool = False,
    ) -> DotDiffResult:
        entries: List[DotDiffEntry] = []
        all_keys = sorted(set(old) | set(new))

        for key in all_keys:
            in_old = key in old
            in_new = key in new

            if in_old and not in_new:
                entries.append(DotDiffEntry(key, old[key], None, "removed"))
            elif in_new and not in_old:
                entries.append(DotDiffEntry(key, None, new[key], "added"))
            else:
                if self._normalise(old[key]) != self._normalise(new[key]):
                    entries.append(DotDiffEntry(key, old[key], new[key], "changed"))
                elif include_unchanged:
                    entries.append(DotDiffEntry(key, old[key], new[key], "unchanged"))

        return DotDiffResult(entries=entries)
