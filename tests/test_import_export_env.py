"""Tests for EnvImporter in envoy/import_export_env.py."""
import json
import pytest

from envoy.import_export_env import EnvImporter, ImportFormat


@pytest.fixture()
def importer():
    return EnvImporter()


class TestFormatDetection:
    def test_detects_dotenv_by_default(self, importer):
        assert importer.detect_format("KEY=value") == ImportFormat.DOTENV

    def test_detects_json_by_brace(self, importer):
        assert importer.detect_format('{"K": "v"}') == ImportFormat.JSON

    def test_hint_overrides_detection(self, importer):
        assert importer.detect_format("KEY=val", hint="json") == ImportFormat.JSON

    def test_invalid_hint_raises(self, importer):
        with pytest.raises(ValueError):
            importer.detect_format("KEY=val", hint="xml")


class TestDotenvImport:
    def test_simple_vars(self, importer):
        result = importer.load("A=1\nB=2\n")
        assert result.vars == {"A": "1", "B": "2"}
        assert result.format == ImportFormat.DOTENV

    def test_comments_ignored(self, importer):
        result = importer.load("# comment\nX=hello\n")
        assert "X" in result.vars
        assert len(result.vars) == 1

    def test_quoted_values(self, importer):
        result = importer.load('Q="hello world"\n')
        assert result.vars["Q"] == "hello world"


class TestJsonImport:
    def test_flat_object(self, importer):
        data = json.dumps({"HOST": "localhost", "PORT": "5432"})
        result = importer.load(data, fmt="json")
        assert result.vars["PORT"] == "5432"
        assert result.format == ImportFormat.JSON

    def test_non_dict_raises(self, importer):
        with pytest.raises(ValueError, match="object"):
            importer.load("[1,2,3]", fmt="json")

    def test_numeric_values_coerced_to_str(self, importer):
        data = json.dumps({"N": 42})
        result = importer.load(data, fmt="json")
        assert result.vars["N"] == "42"


class TestImportResult:
    def test_source_stored(self, importer):
        result = importer.load("A=1", source="myfile.env")
        assert result.source == "myfile.env"

    def test_warnings_list_present(self, importer):
        result = importer.load("A=1")
        assert isinstance(result.warnings, list)
