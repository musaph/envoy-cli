from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CopyChange:
    source_key: str
    dest_key: str
    value: str
    overwritten: bool = False

    def __repr__(self) -> str:
        tag = " (overwritten)" if self.overwritten else ""
        return f"CopyChange({self.source_key!r} -> {self.dest_key!r}{tag})"


@dataclass
class CopyResult:
    changes: List[CopyChange] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def __repr__(self) -> str:
        return (
            f"CopyResult(changes={len(self.changes)}, errors={len(self.errors)})"
        )


class EnvCopier:
    def __init__(self, overwrite: bool = False):
        self.overwrite = overwrite

    def copy(
        self,
        vars: Dict[str, str],
        mappings: Dict[str, str],
    ) -> CopyResult:
        """Copy values from source keys to destination keys.

        Args:
            vars: The current environment variables.
            mappings: A dict mapping source_key -> dest_key.

        Returns:
            CopyResult with applied changes and any errors.
        """
        result = vars.copy()
        changes: List[CopyChange] = []
        errors: List[str] = []

        for src, dst in mappings.items():
            if src not in vars:
                errors.append(f"Source key not found: {src!r}")
                continue
            value = vars[src]
            overwritten = dst in vars
            if overwritten and not self.overwrite:
                errors.append(
                    f"Destination key {dst!r} already exists; use overwrite=True to replace"
                )
                continue
            result[dst] = value
            changes.append(CopyChange(src, dst, value, overwritten=overwritten and self.overwrite))

        return CopyResult(changes=changes, errors=errors)
