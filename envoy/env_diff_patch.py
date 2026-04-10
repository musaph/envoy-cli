"""Patch generation and application for .env variable sets."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PatchOperation:
    op: str  # 'add', 'remove', 'replace'
    key: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"op": self.op, "key": self.key}
        if self.old_value is not None:
            d["old_value"] = self.old_value
        if self.new_value is not None:
            d["new_value"] = self.new_value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "PatchOperation":
        return cls(
            op=data["op"],
            key=data["key"],
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
        )

    def __repr__(self) -> str:
        return f"PatchOperation(op={self.op!r}, key={self.key!r})"


@dataclass
class EnvPatch:
    operations: List[PatchOperation] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.operations) == 0

    def to_dict(self) -> dict:
        return {"operations": [op.to_dict() for op in self.operations]}

    @classmethod
    def from_dict(cls, data: dict) -> "EnvPatch":
        ops = [PatchOperation.from_dict(o) for o in data.get("operations", [])]
        return cls(operations=ops)


class EnvPatcher:
    """Generates and applies patches between two env variable dicts."""

    def generate(self, base: Dict[str, str], target: Dict[str, str]) -> EnvPatch:
        """Produce a patch that transforms base into target."""
        ops: List[PatchOperation] = []
        all_keys = set(base) | set(target)
        for key in sorted(all_keys):
            in_base = key in base
            in_target = key in target
            if in_base and not in_target:
                ops.append(PatchOperation(op="remove", key=key, old_value=base[key]))
            elif not in_base and in_target:
                ops.append(PatchOperation(op="add", key=key, new_value=target[key]))
            elif base[key] != target[key]:
                ops.append(
                    PatchOperation(
                        op="replace",
                        key=key,
                        old_value=base[key],
                        new_value=target[key],
                    )
                )
        return EnvPatch(operations=ops)

    def apply(self, base: Dict[str, str], patch: EnvPatch) -> Tuple[Dict[str, str], List[str]]:
        """Apply patch to base. Returns (result, list_of_conflict_keys)."""
        result = dict(base)
        conflicts: List[str] = []
        for op in patch.operations:
            if op.op == "add":
                if op.key in result:
                    conflicts.append(op.key)
                else:
                    result[op.key] = op.new_value
            elif op.op == "remove":
                if op.key in result and result[op.key] == op.old_value:
                    del result[op.key]
                else:
                    conflicts.append(op.key)
            elif op.op == "replace":
                if result.get(op.key) == op.old_value:
                    result[op.key] = op.new_value
                else:
                    conflicts.append(op.key)
        return result, conflicts
