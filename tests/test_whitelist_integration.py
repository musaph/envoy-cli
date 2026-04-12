import pytest
from envoy.env_whitelist import EnvWhitelist
from envoy.parser import EnvParser
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def whitelist():
    return EnvWhitelist(allowed_keys=["APP_NAME", "APP_ENV", "PORT"])


@pytest.fixture
def exporter():
    return EnvExporter()


RAW_ENV = """
APP_NAME=myapp
APP_ENV=staging
PORT=3000
INTERNAL_SECRET=do_not_expose
DEBUG=true
"""


class TestWhitelistWithParser:
    def test_parse_then_whitelist_filters_correctly(self, parser, whitelist):
        vars_ = parser.parse(RAW_ENV)
        result = whitelist.check(vars_)
        assert "APP_NAME" in result.allowed
        assert "INTERNAL_SECRET" not in result.allowed
        assert any(v.key == "INTERNAL_SECRET" for v in result.violations)

    def test_filter_then_export_shell(self, parser, whitelist, exporter):
        vars_ = parser.parse(RAW_ENV)
        filtered = whitelist.filter(vars_)
        result = exporter.export(filtered, fmt="shell")
        assert "APP_NAME" in result.render
        assert "INTERNAL_SECRET" not in result.render
        assert "DEBUG" not in result.render

    def test_violation_count_matches_unlisted_keys(self, parser, whitelist):
        vars_ = parser.parse(RAW_ENV)
        result = whitelist.check(vars_)
        unlisted = {k for k in vars_ if k not in {"APP_NAME", "APP_ENV", "PORT"}}
        assert len(result.violations) == len(unlisted)

    def test_empty_env_produces_clean_result(self, parser, whitelist):
        vars_ = parser.parse("")
        result = whitelist.check(vars_)
        assert result.is_clean
        assert result.allowed == {}
