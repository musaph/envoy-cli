"""Import and export .env files in multiple formats (dotenv, JSON, YAML)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from envoy.parser import EnvParser


class ImportFormat(str, Enum):
    DOTENV = "dotenv"
    JSON = "json"
    YAML = "yaml"


@dataclass
class ImportResult:
    vars: Dict[str, str]
    format: ImportFormat
    source: str
    warnings: list

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ImportResult format={self.format} vars={len(self.vars)}>"


class EnvImporter:
    """Imports environment variables from various file formats."""

    def __init__(self) -> None:
        self._parser = EnvParser()

    def detect_format(self, content: str, hint: Optional[str] = None) -> ImportFormat:
        """Detect the format of the content or use the provided hint."""
        if hint:
            return ImportFormat(hint.lower())
        stripped = content.strip()
        if stripped.startswith("{"):
            return ImportFormat.JSON
        if any(stripped.startswith(c) for c in ("---", "- ")) and _YAML_AVAILABLE:
            return ImportFormat.YAML
        return ImportFormat.DOTENV

    def from_dotenv(self, content: str) -> Dict[str, str]:
        return self._parser.parse(content)

    def from_json(self, content: str) -> Dict[str, str]:
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")
        return {str(k): str(v) for k, v in data.items()}

    def from_yaml(self, content: str) -> Dict[str, str]:
        if not _YAML_AVAILABLE:
            raise RuntimeError("PyYAML is not installed; run: pip install pyyaml")
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError("YAML root must be a mapping")
        return {str(k): str(v) for k, v in data.items()}

    def load(self, content: str, source: str = "<input>",
             fmt: Optional[str] = None) -> ImportResult:
        """Parse content and return an ImportResult."""
        warnings: list = []
        detected = self.detect_format(content, fmt)
        dispatch = {
            ImportFormat.DOTENV: self.from_dotenv,
            ImportFormat.JSON: self.from_json,
            ImportFormat.YAML: self.from_yaml,
        }
        vars_ = dispatch[detected](content)
        return ImportResult(vars=vars_, format=detected, source=source, warnings=warnings)
