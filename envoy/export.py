"""Export env vars to various shell/CI formats."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


SUPPORTED_FORMATS = ("shell", "docker", "github", "dotenv")


@dataclass
class ExportResult:
    format: str
    lines: List[str]

    def render(self) -> str:
        return "\n".join(self.lines)


class EnvExporter:
    """Convert a dict of env vars into various export formats."""

    def export(self, vars: Dict[str, str], fmt: str) -> ExportResult:
        if fmt not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
            )
        method = getattr(self, f"_export_{fmt}")
        lines = method(vars)
        return ExportResult(format=fmt, lines=lines)

    def _export_shell(self, vars: Dict[str, str]) -> List[str]:
        return [f"export {k}={self._quote(v)}" for k, v in vars.items()]

    def _export_docker(self, vars: Dict[str, str]) -> List[str]:
        return [f"-e {k}={self._quote(v)}" for k, v in vars.items()]

    def _export_github(self, vars: Dict[str, str]) -> List[str]:
        return [f"echo {k}={v} >> $GITHUB_ENV" for k, v in vars.items()]

    def _export_dotenv(self, vars: Dict[str, str]) -> List[str]:
        return [f"{k}={self._quote(v)}" for k, v in vars.items()]

    @staticmethod
    def _quote(value: str) -> str:
        """Wrap value in double quotes if it contains spaces or special chars."""
        needs_quoting = any(c in value for c in (" ", "\t", "$", "'", "\\", "\n"))
        if needs_quoting:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return value
