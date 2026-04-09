"""Integration tests: EnvImporter -> EnvParser -> EnvExporter roundtrip."""
import json
from pathlib import Path

import pytest

from envoy.import_export_env import EnvImporter
from envoy.parser import EnvParser
from envoy.export import EnvExporter


@pytest.fixture()
def importer():
    return EnvImporter()


@pytest.fixture()
def parser():
    return EnvParser()


@pytest.fixture()
def exporter():
    return EnvExporter()


class TestImportParserRoundtrip:
    def test_dotenv_roundtrip(self, importer, parser):
        original = "APP_ENV=production\nDEBUG=false\n"
        result = importer.load(original)
        serialized = parser.serialize(result.vars)
        reparsed = parser.parse(serialized)
        assert reparsed["APP_ENV"] == "production"
        assert reparsed["DEBUG"] == "false"

    def test_json_import_then_serialize(self, importer, parser):
        data = json.dumps({"SECRET_KEY": "abc123", "PORT": "8000"})
        result = importer.load(data, fmt="json")
        serialized = parser.serialize(result.vars)
        reparsed = parser.parse(serialized)
        assert reparsed["SECRET_KEY"] == "abc123"

    def test_import_then_export_docker(self, importer, exporter):
        dotenv_content = "REDIS_URL=redis://localhost:6379\nCACHE_TTL=300\n"
        result = importer.load(dotenv_content)
        export_result = exporter.export(result.vars, fmt="docker")
        assert "--env REDIS_URL=redis://localhost:6379" in export_result.render()

    def test_import_merge_then_export(self, importer, parser, exporter):
        base = importer.load("A=1\nB=2\n")
        override = importer.load("B=99\nC=3\n")
        merged = {**base.vars, **override.vars}
        assert merged["B"] == "99"
        assert merged["A"] == "1"
        shell = exporter.export(merged, fmt="shell")
        assert "export A=" in shell.render()

    def test_empty_dotenv_import(self, importer):
        result = importer.load("# only comments\n\n")
        assert result.vars == {}
