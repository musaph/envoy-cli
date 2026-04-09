"""Template rendering for .env files with variable substitution."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TemplateVariable:
    name: str
    default: Optional[str] = None
    required: bool = True

    def __repr__(self) -> str:
        return f"TemplateVariable(name={self.name!r}, default={self.default!r}, required={self.required})"


# Matches ${VAR_NAME} or ${VAR_NAME:-default}
_PLACEHOLDER_RE = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(?::-(.*?))?\}")


class EnvTemplate:
    """Renders an env template string by substituting placeholders."""

    def __init__(self, template: str) -> None:
        self.template = template

    def variables(self) -> List[TemplateVariable]:
        """Return all variables referenced in the template."""
        seen: Dict[str, TemplateVariable] = {}
        for match in _PLACEHOLDER_RE.finditer(self.template):
            name, default = match.group(1), match.group(2)
            if name not in seen:
                seen[name] = TemplateVariable(
                    name=name,
                    default=default,
                    required=default is None,
                )
        return list(seen.values())

    def render(self, context: Dict[str, str]) -> str:
        """Substitute placeholders with values from *context*.

        Raises KeyError if a required variable is missing.
        """
        missing = [
            v.name
            for v in self.variables()
            if v.required and v.name not in context
        ]
        if missing:
            raise KeyError(f"Missing required template variables: {missing}")

        def _replace(m: re.Match) -> str:
            name, default = m.group(1), m.group(2)
            return context.get(name, default or "")

        return _PLACEHOLDER_RE.sub(_replace, self.template)

    def missing_variables(self, context: Dict[str, str]) -> List[str]:
        """Return names of required variables absent from *context*."""
        return [
            v.name
            for v in self.variables()
            if v.required and v.name not in context
        ]
