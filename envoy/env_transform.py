"""Apply value transformations to environment variables."""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class TransformChange:
    key: str
    original: str
    transformed: str

    def __repr__(self) -> str:
        return f"TransformChange(key={self.key!r}, {self.original!r} -> {self.transformed!r})"


@dataclass
class TransformResult:
    vars: Dict[str, str]
    changes: List[TransformChange] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def __repr__(self) -> str:
        return (
            f"TransformResult(changes={len(self.changes)}, "
            f"errors={len(self.errors)})"
        )


BUILTIN_TRANSFORMS: Dict[str, Callable[[str], str]] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "trim_quotes": lambda v: v.strip("'\"\u201c\u201d"),
    "to_bool": lambda v: "true" if v.lower() in ("1", "yes", "on", "true") else "false",
}


class EnvTransformer:
    """Apply named or custom transforms to env var values."""

    def __init__(self, custom: Optional[Dict[str, Callable[[str], str]]] = None):
        self._transforms: Dict[str, Callable[[str], str]] = dict(BUILTIN_TRANSFORMS)
        if custom:
            self._transforms.update(custom)

    def available(self) -> List[str]:
        return sorted(self._transforms.keys())

    def transform(
        self,
        vars: Dict[str, str],
        transform_name: str,
        keys: Optional[List[str]] = None,
    ) -> TransformResult:
        if transform_name not in self._transforms:
            return TransformResult(
                vars=dict(vars),
                errors=[f"Unknown transform: {transform_name!r}"],
            )

        fn = self._transforms[transform_name]
        target_keys = keys if keys is not None else list(vars.keys())
        result_vars = dict(vars)
        changes: List[TransformChange] = []
        errors: List[str] = []

        for key in target_keys:
            if key not in vars:
                errors.append(f"Key not found: {key!r}")
                continue
            original = vars[key]
            try:
                transformed = fn(original)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Transform failed for {key!r}: {exc}")
                continue
            if transformed != original:
                result_vars[key] = transformed
                changes.append(TransformChange(key=key, original=original, transformed=transformed))

        return TransformResult(vars=result_vars, changes=changes, errors=errors)
