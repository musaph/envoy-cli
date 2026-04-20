from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class UppercaseKeyChange:
    original_key: str
    new_key: str
    value: str

    def __repr__(self) -> str:
        return f"<UppercaseKeyChange {self.original_key!r} -> {self.new_key!r}>"


@dataclass
class UppercaseKeyResult:
    changes: List[UppercaseKeyChange] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"<UppercaseKeyResult changes={len(self.changes)} "
            f"skipped={len(self.skipped)}>"
        )

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [c.original_key for c in self.changes]

    @property
    def output_vars(self) -> Dict[str, str]:
        result = {}
        for change in self.changes:
            result[change.new_key] = change.value
        return result


class EnvUppercaseKeyConverter:
    """Converts all environment variable keys to UPPER_CASE."""

    def __init__(self, overwrite: bool = False):
        self._overwrite = overwrite

    def convert(self, vars: Dict[str, str]) -> UppercaseKeyResult:
        changes: List[UppercaseKeyChange] = []
        skipped: List[str] = []
        seen_upper: Dict[str, str] = {}

        for key, value in vars.items():
            upper_key = key.upper()
            if upper_key == key:
                seen_upper[upper_key] = value
                continue
            if upper_key in seen_upper and not self._overwrite:
                skipped.append(key)
                continue
            changes.append(UppercaseKeyChange(
                original_key=key,
                new_key=upper_key,
                value=value,
            ))
            seen_upper[upper_key] = value

        return UppercaseKeyResult(changes=changes, skipped=skipped)
