"""Fill placeholder values in .env files from a context dictionary."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

_PLACEHOLDER_RE = re.compile(r"<([A-Z0-9_]+)(?::([^>]*))?>") 


@dataclass
class FillChange:
    key: str
    old_value: str
    new_value: str
    used_default: bool = False

    def __repr__(self) -> str:
        tag = " (default)" if self.used_default else ""
        return f"FillChange({self.key}: {self.old_value!r} -> {self.new_value!r}{tag})"


@dataclass
class FillResult:
    changes: List[FillChange] = field(default_factory=list)
    unfilled: List[str] = field(default_factory=list)
    output: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    @property
    def is_complete(self) -> bool:
        return not self.unfilled

    def __repr__(self) -> str:
        return (
            f"FillResult(changes={len(self.changes)}, "
            f"unfilled={len(self.unfilled)}, "
            f"complete={self.is_complete})"
        )


class EnvPlaceholderFiller:
    """Fills placeholder tokens in env var values from a context dict."""

    def __init__(self, strict: bool = False):
        """Args:
            strict: If True, raise ValueError when a placeholder has no fill
                    value and no default.
        """
        self.strict = strict

    def fill(self, vars: Dict[str, str], context: Dict[str, str]) -> FillResult:
        """Replace placeholders in *vars* values using *context*.

        Placeholder syntax: ``<VAR_NAME>`` or ``<VAR_NAME:default>``.
        """
        result = FillResult()
        output: Dict[str, str] = {}

        for key, value in vars.items():
            new_value, changes, missing = self._process_value(key, value, context)
            output[key] = new_value
            result.changes.extend(changes)
            result.unfilled.extend(missing)

        if self.strict and result.unfilled:
            raise ValueError(
                f"Unfilled placeholders in keys: {result.unfilled}"
            )

        result.output = output
        return result

    # ------------------------------------------------------------------
    def _process_value(
        self,
        key: str,
        value: str,
        context: Dict[str, str],
    ):
        changes: List[FillChange] = []
        missing: List[str] = []
        original = value

        def _replace(m: re.Match) -> str:
            name = m.group(1)
            default: Optional[str] = m.group(2)  # None when no colon present
            if name in context:
                changes.append(
                    FillChange(key=key, old_value=original, new_value="", used_default=False)
                )
                return context[name]
            if default is not None:
                changes.append(
                    FillChange(key=key, old_value=original, new_value="", used_default=True)
                )
                return default
            missing.append(key)
            return m.group(0)  # leave placeholder intact

        new_value = _PLACEHOLDER_RE.sub(_replace, value)
        # Patch new_value into changes now that we have it
        for ch in changes:
            ch.new_value = new_value
        return new_value, changes, missing
