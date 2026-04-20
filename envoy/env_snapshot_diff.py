"""Compare two snapshots and produce a structured diff."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envoy.snapshot import Snapshot


@dataclass
class SnapshotDiffEntry:
    key: str
    status: str  # 'added' | 'removed' | 'changed' | 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __repr__(self) -> str:
        return f"SnapshotDiffEntry(key={self.key!r}, status={self.status!r})"


@dataclass
class SnapshotDiffResult:
    entries: List[SnapshotDiffEntry] = field(default_factory=list)
    old_label: str = ""
    new_label: str = ""

    def added(self) -> List[SnapshotDiffEntry]:
        return [e for e in self.entries if e.status == "added"]

    def removed(self) -> List[SnapshotDiffEntry]:
        return [e for e in self.entries if e.status == "removed"]

    def changed(self) -> List[SnapshotDiffEntry]:
        return [e for e in self.entries if e.status == "changed"]

    def unchanged(self) -> List[SnapshotDiffEntry]:
        return [e for e in self.entries if e.status == "unchanged"]

    def has_diff(self) -> bool:
        return any(e.status != "unchanged" for e in self.entries)

    def __repr__(self) -> str:
        return (
            f"SnapshotDiffResult(added={len(self.added())}, "
            f"removed={len(self.removed())}, changed={len(self.changed())})"
        )


class SnapshotDiffer:
    """Diffs two Snapshot objects key-by-key."""

    def diff(self, old: Snapshot, new: Snapshot) -> SnapshotDiffResult:
        result = SnapshotDiffResult(
            old_label=old.label or old.snapshot_id,
            new_label=new.label or new.snapshot_id,
        )
        all_keys = set(old.vars.keys()) | set(new.vars.keys())
        for key in sorted(all_keys):
            in_old = key in old.vars
            in_new = key in new.vars
            if in_old and not in_new:
                result.entries.append(
                    SnapshotDiffEntry(key=key, status="removed", old_value=old.vars[key])
                )
            elif in_new and not in_old:
                result.entries.append(
                    SnapshotDiffEntry(key=key, status="added", new_value=new.vars[key])
                )
            elif old.vars[key] != new.vars[key]:
                result.entries.append(
                    SnapshotDiffEntry(
                        key=key,
                        status="changed",
                        old_value=old.vars[key],
                        new_value=new.vars[key],
                    )
                )
            else:
                result.entries.append(
                    SnapshotDiffEntry(
                        key=key,
                        status="unchanged",
                        old_value=old.vars[key],
                        new_value=new.vars[key],
                    )
                )
        return result
