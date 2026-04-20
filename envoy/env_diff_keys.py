"""Compute key-level differences between two env var dicts."""
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class DiffKeysEntry:
    key: str
    status: str  # 'added', 'removed', 'common'

    def __repr__(self) -> str:
        return f"DiffKeysEntry(key={self.key!r}, status={self.status!r})"


@dataclass
class DiffKeysResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    common: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"DiffKeysResult(added={len(self.added)}, "
            f"removed={len(self.removed)}, common={len(self.common)})"
        )

    @property
    def has_diff(self) -> bool:
        return bool(self.added or self.removed)

    @property
    def entries(self) -> List[DiffKeysEntry]:
        result = []
        for k in sorted(self.added):
            result.append(DiffKeysEntry(k, "added"))
        for k in sorted(self.removed):
            result.append(DiffKeysEntry(k, "removed"))
        for k in sorted(self.common):
            result.append(DiffKeysEntry(k, "common"))
        return result


class EnvDiffKeys:
    def compare(
        self,
        old: Dict[str, str],
        new: Dict[str, str],
    ) -> DiffKeysResult:
        old_keys: Set[str] = set(old.keys())
        new_keys: Set[str] = set(new.keys())
        return DiffKeysResult(
            added=sorted(new_keys - old_keys),
            removed=sorted(old_keys - new_keys),
            common=sorted(old_keys & new_keys),
        )

    def only_in_old(
        self, old: Dict[str, str], new: Dict[str, str]
    ) -> Dict[str, str]:
        removed = set(old.keys()) - set(new.keys())
        return {k: old[k] for k in removed}

    def only_in_new(
        self, old: Dict[str, str], new: Dict[str, str]
    ) -> Dict[str, str]:
        added = set(new.keys()) - set(old.keys())
        return {k: new[k] for k in added}
