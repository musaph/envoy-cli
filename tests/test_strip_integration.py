"""Integration tests for EnvStripper with EnvParser and EnvExporter."""
import pytest
from envoy.env_strip import EnvStripper
from envoy.parser import EnvParser
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def stripper():
    return EnvStripper(prefix="dev_")


@pytest.fixture
def exporter():
    return EnvExporter()


@pytest.fixture
def sample_env_content():
    return "dev_HOST=dev_localhost\ndev_PORT=dev_8080\nAPP_ENV=development\n"


class TestStripWithParser:
    def test_parse_then_strip_removes_prefix(self, parser, stripper, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        result = stripper.strip(vars_)
        assert result.has_changes()
        changed = result.changed_keys()
        assert "dev_HOST" in changed
        assert "dev_PORT" in changed

    def test_parse_then_apply_modifies_values(self, parser, stripper, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        out = stripper.apply(vars_)
        assert out["dev_HOST"] == "localhost"
        assert out["dev_PORT"] == "8080"
        assert out["APP_ENV"] == "development"  # unchanged

    def test_strip_then_export_roundtrip(self, parser, stripper, exporter, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        stripped = stripper.apply(vars_)
        shell_output = exporter.export(stripped, fmt="shell")
        assert "localhost" in shell_output
        assert "8080" in shell_output

    def test_no_match_leaves_all_unchanged(self, parser, exporter):
        content = "HOST=localhost\nPORT=8080\n"
        stripper = EnvStripper(prefix="prod_")
        vars_ = parser.parse(content)
        result = stripper.strip(vars_)
        assert not result.has_changes()
        assert set(result.unchanged) == {"HOST", "PORT"}
