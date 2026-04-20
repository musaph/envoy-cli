"""Integration tests: EnvSwapper with EnvParser and EnvExporter."""
import pytest
from envoy.env_swap import EnvSwapper
from envoy.parser import EnvParser
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def swapper():
    return EnvSwapper()


@pytest.fixture
def exporter():
    return EnvExporter()


class TestSwapWithParser:
    def test_parse_then_swap_roundtrip(self, parser, swapper):
        content = "HOST=localhost\nPORT=5432\n"
        vars_ = parser.parse(content)
        result = swapper.swap(vars_)
        # swapped: localhost=HOST, 5432=PORT
        assert result.vars.get("localhost") == "HOST"
        assert result.vars.get("5432") == "PORT"

    def test_double_swap_restores_original(self, parser, swapper):
        content = "HOST=localhost\nPORT=5432\n"
        vars_ = parser.parse(content)
        once = swapper.swap(vars_).vars
        twice = swapper.swap(once).vars
        assert twice == vars_

    def test_swap_then_export_shell(self, parser, swapper, exporter):
        vars_ = parser.parse("DB=postgres\n")
        swapped = swapper.swap(vars_).vars
        export_result = exporter.export(swapped, fmt="shell")
        assert "postgres" in export_result.render
        assert "DB" in export_result.render

    def test_empty_values_excluded_from_swap(self, parser, swapper):
        content = "EMPTY=\nNAME=alice\n"
        vars_ = parser.parse(content)
        result = swapper.swap(vars_)
        assert "EMPTY" in result.skipped
        assert "alice" in result.vars
        assert "" not in result.vars
