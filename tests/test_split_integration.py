"""Integration tests combining EnvSplitter with EnvParser and EnvExporter."""
import pytest
from envoy.env_split import EnvSplitter
from envoy.parser import EnvParser
from envoy.export import EnvExporter


@pytest.fixture()
def parser() -> EnvParser:
    return EnvParser()


@pytest.fixture()
def splitter() -> EnvSplitter:
    return EnvSplitter(strip_prefix=True)


@pytest.fixture()
def exporter() -> EnvExporter:
    return EnvExporter()


ENV_CONTENT = """\
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb
REDIS_HOST=redis
REDIS_PORT=6379
APP_NAME=envoy
DEBUG=false
"""


class TestSplitWithParser:
    def test_parse_then_split_groups_correctly(self, parser, splitter):
        vars = parser.parse(ENV_CONTENT)
        result = splitter.split(vars, ["DB_", "REDIS_"])
        assert result.groups["DB_"]["HOST"] == "localhost"
        assert result.groups["DB_"]["NAME"] == "mydb"
        assert result.groups["REDIS_"]["HOST"] == "redis"

    def test_unmatched_vars_isolated(self, parser, splitter):
        vars = parser.parse(ENV_CONTENT)
        result = splitter.split(vars, ["DB_", "REDIS_"])
        assert "APP_NAME" in result.unmatched
        assert "DEBUG" in result.unmatched
        assert len(result.unmatched) == 2

    def test_split_and_export_shell_format(self, parser, splitter, exporter):
        vars = parser.parse(ENV_CONTENT)
        result = splitter.split(vars, ["DB_"])
        db_vars = result.groups.get("DB_", {})
        export_result = exporter.export(db_vars, fmt="shell")
        assert "export HOST=" in export_result.render
        assert "export PORT=" in export_result.render

    def test_default_group_then_export(self, parser, splitter, exporter):
        vars = parser.parse(ENV_CONTENT)
        result = splitter.split(vars, ["DB_"], default_group="rest")
        rest_vars = result.groups.get("rest", {})
        export_result = exporter.export(rest_vars, fmt="dotenv")
        assert "APP_NAME" in export_result.render
        assert "DEBUG" in export_result.render
