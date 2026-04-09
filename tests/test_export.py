"""Unit tests for envoy.export."""
import pytest
from envoy.export import EnvExporter, ExportResult, SUPPORTED_FORMATS


@pytest.fixture
def exporter():
    return EnvExporter()


@pytest.fixture
def simple_vars():
    return {"APP_ENV": "production", "PORT": "8080", "DEBUG": "false"}


class TestEnvExporter:
    def test_export_shell_format(self, exporter, simple_vars):
        result = exporter.export(simple_vars, "shell")
        assert isinstance(result, ExportResult)
        assert result.format == "shell"
        assert "export APP_ENV=production" in result.lines
        assert "export PORT=8080" in result.lines

    def test_export_docker_format(self, exporter, simple_vars):
        result = exporter.export(simple_vars, "docker")
        assert "-e APP_ENV=production" in result.lines
        assert "-e PORT=8080" in result.lines

    def test_export_github_format(self, exporter, simple_vars):
        result = exporter.export(simple_vars, "github")
        assert "echo APP_ENV=production >> $GITHUB_ENV" in result.lines

    def test_export_dotenv_format(self, exporter, simple_vars):
        result = exporter.export(simple_vars, "dotenv")
        assert "APP_ENV=production" in result.lines

    def test_unsupported_format_raises(self, exporter, simple_vars):
        with pytest.raises(ValueError, match="Unsupported format"):
            exporter.export(simple_vars, "xml")

    def test_render_joins_lines(self, exporter, simple_vars):
        result = exporter.export(simple_vars, "shell")
        rendered = result.render()
        assert "\n" in rendered
        assert "export APP_ENV=production" in rendered

    def test_value_with_spaces_is_quoted(self, exporter):
        result = exporter.export({"MSG": "hello world"}, "shell")
        assert 'export MSG="hello world"' in result.lines

    def test_value_with_dollar_is_quoted(self, exporter):
        result = exporter.export({"PATH": "/usr/bin:$HOME/bin"}, "shell")
        assert result.lines[0].startswith("export PATH=\"")

    def test_plain_value_not_quoted(self, exporter):
        result = exporter.export({"KEY": "simple"}, "shell")
        assert result.lines[0] == "export KEY=simple"

    def test_all_formats_are_supported(self, exporter):
        vars_ = {"X": "1"}
        for fmt in SUPPORTED_FORMATS:
            result = exporter.export(vars_, fmt)
            assert len(result.lines) == 1
