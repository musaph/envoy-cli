"""Integration tests: EnvFormatter + EnvParser roundtrip."""
import pytest
from envoy.env_format import EnvFormatter
from envoy.parser import EnvParser


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def formatter():
    return EnvFormatter()


class TestFormatterWithParser:
    def test_parse_then_format_uppercases_keys(self, parser, formatter):
        raw = "db_host=localhost\ndb_port=5432\n"
        vars_ = parser.parse(raw)
        result = formatter.format(vars_)
        assert "DB_HOST" in result.vars
        assert "DB_PORT" in result.vars

    def test_format_then_serialize_roundtrip(self, parser, formatter):
        raw = "api_key=  my_secret  \napp_env=production\n"
        vars_ = parser.parse(raw)
        result = formatter.format(vars_)
        serialized = parser.serialize(result.vars)
        reparsed = parser.parse(serialized)
        assert reparsed["API_KEY"] == "my_secret"
        assert reparsed["APP_ENV"] == "production"

    def test_remove_empty_then_serialize(self, parser):
        f = EnvFormatter(remove_empty=True)
        raw = "KEY=value\nEMPTY=\nOTHER=hello\n"
        vars_ = parser.parse(raw)
        result = f.format(vars_)
        assert "EMPTY" not in result.vars
        serialized = parser.serialize(result.vars)
        assert "EMPTY" not in serialized

    def test_quote_values_survive_parse(self, parser):
        f = EnvFormatter(quote_values=True, strip_values=True)
        vars_ = {"KEY": "value"}
        result = f.format(vars_)
        serialized = parser.serialize(result.vars)
        reparsed = parser.parse(serialized)
        # Parser should strip surrounding quotes
        assert "value" in reparsed.get("KEY", "")

    def test_no_changes_on_already_formatted_input(self, parser, formatter):
        raw = "KEY=value\nOTHER=data\n"
        vars_ = parser.parse(raw)
        result = formatter.format(vars_)
        assert not result.has_changes
        assert not result.skipped
