"""Rename keys in .env variable sets with optional dry-run support."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class RenameOperation:
    old_key: str
    new_key: str
    value: Optional[str] = None

    def to_dict(self) -> dict:
        return {"old_key": self.old_key, "new_key": self.new_key, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> "RenameOperation":
        return cls(
            old_key=data["old_key"],
            new_key=data["new_key"],
            value=data.get("value"),
        )

    def __repr__(self) -> str:
        return f"RenameOperation({self.old_key!r} -> {self.new_key!r})"


@dataclass
class RenameResult:
    applied: List[RenameOperation] = field(default_factory=list)
    skipped: List[Tuple[str, str]] = field(default_factory=list)  # (key, reason)
    vars: Dict[str, str] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return len(self.skipped) == 0

    def __repr__(self) -> str:
        return (
            f"RenameResult(applied={len(self.applied)}, "
            f"skipped={len(self.skipped)}, success={self.success})"
        )


class EnvRenamer:
    """Renames keys within a dict of env vars."""

    def rename(
        self,
        vars: Dict[str, str],
        operations: List[RenameOperation],
        overwrite: bool = False,
    ) -> RenameResult:
        """Apply rename operations to vars. Returns a RenameResult."""
        result_vars = dict(vars)
        applied: List[RenameOperation] = []
        skipped: List[Tuple[str, str]] = []

        for op in operations:
            if op.old_key not in result_vars:
                skipped.append((op.old_key, "key not found"))
                continue
            if op.new_key in result_vars and not overwrite:
                skipped.append((op.new_key, "target key already exists"))
                continue
            if op.old_key == op.new_key:
                skipped.append((op.old_key, "old and new key are identical"))
                continue

            value = result_vars.pop(op.old_key)
            result_vars[op.new_key] = value
            applied.append(RenameOperation(old_key=op.old_key, new_key=op.new_key, value=value))

        return RenameResult(applied=applied, skipped=skipped, vars=result_vars)

    def build_operations(self, pairs: List[Tuple[str, str]]) -> List[RenameOperation]:
        """Build RenameOperation list from (old, new) tuples."""
        return [RenameOperation(old_key=old, new_key=new) for old, new in pairs]
