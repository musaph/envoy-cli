"""Clone (deep-copy) an env variable set with optional key transformations."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CloneResult:
    cloned: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    renamed: Dict[str, str] = field(default_factory=dict)  # old_key -> new_key

    def __repr__(self) -> str:
        return (
            f"CloneResult(cloned={len(self.cloned)}, "
            f"skipped={len(self.skipped)}, renamed={len(self.renamed)})"
        )

    @property
    def has_renames(self) -> bool:
        return bool(self.renamed)


class EnvCloner:
    """Clone an env var mapping with optional prefix stripping/adding and key renaming."""

    def __init__(
        self,
        strip_prefix: Optional[str] = None,
        add_prefix: Optional[str] = None,
        rename_map: Optional[Dict[str, str]] = None,
        skip_keys: Optional[List[str]] = None,
    ) -> None:
        self.strip_prefix = strip_prefix or ""
        self.add_prefix = add_prefix or ""
        self.rename_map: Dict[str, str] = rename_map or {}
        self.skip_keys: List[str] = skip_keys or []

    def clone(self, vars: Dict[str, str]) -> CloneResult:
        result = CloneResult()
        for key, value in vars.items():
            if key in self.skip_keys:
                result.skipped.append(key)
                continue

            new_key = key

            # Apply strip_prefix
            if self.strip_prefix and new_key.startswith(self.strip_prefix):
                new_key = new_key[len(self.strip_prefix):]

            # Apply rename_map (on the possibly-stripped key)
            if new_key in self.rename_map:
                mapped = self.rename_map[new_key]
                result.renamed[new_key] = mapped
                new_key = mapped

            # Apply add_prefix
            if self.add_prefix:
                new_key = self.add_prefix + new_key

            result.cloned[new_key] = value

        return result
