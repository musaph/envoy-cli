"""Integration tests: EnvInheritor + EnvParser + EnvExporter."""
from pathlib import Path
import pytest

from envoy.env_inherit import EnvInheritor
from envoy.parser import EnvParser
from envoy.export import EnvExporter


@pytest.fixture
def parser() -> EnvParser:
    return EnvParser()


@pytest.fixture
def inheritor() -> EnvInheritor:
    return EnvInheritor()


@pytest.fixture
def exporter() -> EnvExporter:
    return EnvExporter()


BASE_ENV = """APP_ENV=production
DB_HOST=db.prod
LOG_LEVEL=warn
SHARED=base_shared
"""

CHILD_ENV = """APP_ENV=staging
EXTRA_KEY=hello
SHARED=child_shared
"""


class TestInheritWithParser:
    def test_parse_then_inherit_merges_correctly(self, parser, inheritor):
        base = parser.parse(BASE_ENV)
        child = parser.parse(CHILD_ENV)
        result = inheritor.inherit(base, child)
        assert result.vars["APP_ENV"] == "staging"
        assert result.vars["DB_HOST"] == "db.prod"
        assert result.vars["LOG_LEVEL"] == "warn"
        assert result.vars["EXTRA_KEY"] == "hello"
        assert result.vars["SHARED"] == "child_shared"

    def test_all_base_keys_present_when_child_is_empty(self, parser, inheritor):
        base = parser.parse(BASE_ENV)
        result = inheritor.inherit(base, {})
        assert set(result.vars.keys()) == set(base.keys())

    def test_inherited_keys_count_is_correct(self, parser, inheritor):
        base = parser.parse(BASE_ENV)
        child = parser.parse(CHILD_ENV)
        result = inheritor.inherit(base, child)
        # DB_HOST and LOG_LEVEL come only from base
        assert "DB_HOST" in result.inherited_keys
        assert "LOG_LEVEL" in result.inherited_keys

    def test_export_after_inherit_produces_valid_dotenv(self, parser, inheritor, exporter):
        base = parser.parse(BASE_ENV)
        child = parser.parse(CHILD_ENV)
        result = inheritor.inherit(base, child)
        exported = exporter.export(result.vars, fmt="dotenv")
        assert "APP_ENV=staging" in exported.render
        assert "DB_HOST=db.prod" in exported.render
