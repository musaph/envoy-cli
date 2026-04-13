"""Summarise differences between two env variable sets."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiffSummaryEntry:
    key: str
    status: str          # 'added' | 'removed' | 'changed' | 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __repr__(self) -> str:
        return f"DiffSummaryEntry(key={self.key!r}, status={self.status!r})"


@dataclass
class DiffSummaryResult:
    entries: List[DiffSummaryEntry] = field(default_factory=list)

    @property
    def added(self) -> List[DiffSummaryEntry]:
        return [e for e in self.entries if e.status == "added"]

    @property
    def removed(self) -> List[DiffSummaryEntry]:
        return [e for e in self.entries if e.status == "removed"]

    @property
    def changed(self) -> List[DiffSummaryEntry]:
        return [e for e in self.entries if e.status == "changed"]

    @property
    def unchanged(self) -> List[DiffSummaryEntry]:
        return [e for e in self.entries if e.status == "unchanged"]

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def __repr__(self) -> str:
        return (
            f"DiffSummaryResult(added={len(self.added)}, removed={len(self.removed)}, "
            f"changed={len(self.changed)}, unchanged={len(self.unchanged)})"
        )


class EnvDiffSummarizer:
    """Compare two dicts of env vars and produce a structured DiffSummaryResult."""

    def __init__(self, ignore_case: bool = False):
        self.ignore_case = ignore_case

    def _normalise(self, value: str) -> str:
        return value.lower() if self.ignore_case else value

    def summarise(
        self,
        old: Dict[str, str],
        new: Dict[str, str],
    ) -> DiffSummaryResult:
        entries: List[DiffSummaryEntry] = []
        all_keys = sorted(set(old) | set(new))

        for key in all_keys:
            if key in old and key not in new:
                entries.append(DiffSummaryEntry(key=key, status="removed", old_value=old[key]))
            elif key not in old and key in new:
                entries.append(DiffSummaryEntry(key=key, status="added", new_value=new[key]))
            elif self._normalise(old[key]) != self._normalise(new[key]):
                entries.append(
                    DiffSummaryEntry(key=key, status="changed", old_value=old[key], new_value=new[key])
                )
            else:
                entries.append(
                    DiffSummaryEntry(key=key, status="unchanged", old_value=old[key], new_value=new[key])
                )

        return DiffSummaryResult(entries=entries)
