"""Integration tests: EnvParser + EnvPlaceholderFiller + EnvParser.serialize."""
import pytest
from envoy.parser import EnvParser
from envoy.env_placeholder_fill import EnvPlaceholderFiller


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def filler():
    return EnvPlaceholderFiller()


SAMPLE_ENV = """
# Database
DB_HOST=<DB_HOST>
DB_PORT=<DB_PORT:5432>
DB_NAME=mydb

# API
API_URL=https://<API_HOST>/v1
DEBUG=false
"""


class TestPlaceholderFillWithParser:
    def test_parse_then_fill_replaces_all_known(self, parser, filler):
        vars = parser.parse(SAMPLE_ENV)
        context = {"DB_HOST": "db.prod.local", "API_HOST": "api.prod.local"}
        result = filler.fill(vars, context)
        assert result.output["DB_HOST"] == "db.prod.local"
        assert result.output["DB_PORT"] == "5432"  # default
        assert result.output["API_URL"] == "https://api.prod.local/v1"
        assert result.output["DB_NAME"] == "mydb"  # untouched

    def test_fill_then_serialize_roundtrip(self, parser, filler):
        vars = parser.parse(SAMPLE_ENV)
        context = {"DB_HOST": "localhost", "API_HOST": "localhost"}
        result = filler.fill(vars, context)
        serialized = parser.serialize(result.output)
        reparsed = parser.parse(serialized)
        assert reparsed["DB_HOST"] == "localhost"
        assert reparsed["DB_PORT"] == "5432"

    def test_unfilled_placeholders_preserved_in_output(self, parser, filler):
        vars = parser.parse("HOST=<HOST>\nPORT=<PORT:8080>\n")
        result = filler.fill(vars, {})  # no context at all
        assert result.output["HOST"] == "<HOST>"
        assert result.output["PORT"] == "8080"  # default used
        assert "HOST" in result.unfilled
        assert "PORT" not in result.unfilled

    def test_plain_vars_not_reported_as_changes(self, parser, filler):
        vars = parser.parse("APP=myapp\nENV=production\n")
        result = filler.fill(vars, {})
        assert not result.has_changes
        assert result.is_complete
