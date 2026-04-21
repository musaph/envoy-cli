import pytest
from envoy.env_wrap import EnvWrapper
from envoy.parser import EnvParser
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def wrapper():
    return EnvWrapper(width=20)


@pytest.fixture
def exporter():
    return EnvExporter()


@pytest.fixture
def sample_env_content():
    return (
        "SHORT=hi\n"
        "MEDIUM=hello_world_here\n"
        "LONG=this_is_a_very_long_value_that_exceeds_the_wrap_width_limit\n"
    )


class TestWrapWithParser:
    def test_parse_then_wrap_detects_long_values(self, parser, wrapper, sample_env_content):
        vars = parser.parse(sample_env_content)
        result = wrapper.wrap(vars)
        assert result.has_changes()
        assert "LONG" in result.changed_keys()

    def test_short_values_unchanged_after_wrap(self, parser, wrapper, sample_env_content):
        vars = parser.parse(sample_env_content)
        out = wrapper.apply(vars)
        assert out["SHORT"] == "hi"

    def test_wrap_then_export_produces_output(self, parser, wrapper, exporter, sample_env_content):
        vars = parser.parse(sample_env_content)
        wrapped = wrapper.apply(vars)
        export_result = exporter.export(wrapped, fmt="dotenv")
        assert export_result.content
        assert "SHORT" in export_result.content

    def test_no_skip_wraps_all_long(self, parser, sample_env_content):
        vars = parser.parse(sample_env_content)
        w = EnvWrapper(width=10)
        result = w.wrap(vars)
        long_keys = [k for k, v in vars.items() if len(v) > 10]
        for k in long_keys:
            assert k in result.changed_keys()
