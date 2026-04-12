"""Promote env vars from one environment profile to another."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PromoteChange:
    key: str
    source_value: str
    target_value: Optional[str]  # None if key didn't exist in target
    overwritten: bool = False

    def __repr__(self) -> str:
        action = "overwrite" if self.overwritten else "add"
        return f"<PromoteChange key={self.key!r} action={action}>"


@dataclass
class PromoteResult:
    added: List[PromoteChange] = field(default_factory=list)
    overwritten: List[PromoteChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.overwritten)

    def __repr__(self) -> str:
        return (
            f"<PromoteResult added={len(self.added)} "
            f"overwritten={len(self.overwritten)} "
            f"skipped={len(self.skipped)}>"
        )


class EnvPromoter:
    """Promotes variables from a source env dict into a target env dict."""

    def __init__(self, overwrite: bool = False, keys: Optional[List[str]] = None):
        """
        Args:
            overwrite: If True, existing keys in target are overwritten.
            keys: Optional allowlist of keys to promote. Promotes all if None.
        """
        self.overwrite = overwrite
        self.keys = set(keys) if keys else None

    def promote(
        self,
        source: Dict[str, str],
        target: Dict[str, str],
    ) -> PromoteResult:
        """Return a PromoteResult and the merged target dict."""
        result = PromoteResult()
        merged = dict(target)

        candidates = {
            k: v for k, v in source.items()
            if self.keys is None or k in self.keys
        }

        for key, value in candidates.items():
            if key in target:
                if self.overwrite:
                    change = PromoteChange(
                        key=key,
                        source_value=value,
                        target_value=target[key],
                        overwritten=True,
                    )
                    result.overwritten.append(change)
                    merged[key] = value
                else:
                    result.skipped.append(key)
            else:
                change = PromoteChange(
                    key=key,
                    source_value=value,
                    target_value=None,
                )
                result.added.append(change)
                merged[key] = value

        return result, merged
