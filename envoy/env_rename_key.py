from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RenameKeyChange:
    old_key: str
    new_key: str
    value: str

    def __repr__(self) -> str:
        return f"RenameKeyChange({self.old_key!r} -> {self.new_key!r})"


@dataclass
class RenameKeyResult:
    changes: List[RenameKeyChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def renamed_keys(self) -> List[str]:
        return [c.old_key for c in self.changes]

    def __repr__(self) -> str:
        return (
            f"RenameKeyResult(changes={len(self.changes)}, "
            f"skipped={len(self.skipped)}, errors={len(self.errors)})"
        )


class EnvKeyRenamer:
    def __init__(self, overwrite: bool = False):
        self.overwrite = overwrite

    def rename(self, vars: Dict[str, str], mapping: Dict[str, str]) -> RenameKeyResult:
        """Rename keys in vars according to mapping {old_key: new_key}."""
        result = RenameKeyResult()
        output = dict(vars)

        for old_key, new_key in mapping.items():
            if old_key not in output:
                result.skipped.append(old_key)
                continue

            if new_key in output and not self.overwrite:
                result.errors.append(
                    f"Cannot rename {old_key!r} to {new_key!r}: target key already exists"
                )
                continue

            if old_key == new_key:
                result.skipped.append(old_key)
                continue

            value = output.pop(old_key)
            output[new_key] = value
            result.changes.append(RenameKeyChange(old_key=old_key, new_key=new_key, value=value))

        return result

    def apply(self, vars: Dict[str, str], mapping: Dict[str, str]) -> Dict[str, str]:
        """Return a new dict with keys renamed per mapping. Skips errors silently."""
        result = self.rename(vars, mapping)
        output = dict(vars)
        for change in result.changes:
            value = output.pop(change.old_key, None)
            if value is not None:
                output[change.new_key] = value
        return output
