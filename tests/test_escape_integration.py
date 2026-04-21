import pytest
from envoy.parser import EnvParser
from envoy.env_escape import EnvEscaper
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def escaper():
    return EnvEscaper()


@pytest.fixture
def unescaper():
    return EnvEscaper(unescape=True)


@pytest.fixture
def exporter():
    return EnvExporter()


@pytest.fixture
def sample_env_content():
    return (
        'NAME=Alice\n'
        'GREETING=Hello World\n'
        'PATH_VAL=/usr/local/bin\n'
        'SIMPLE=no_special_chars\n'
    )


class TestEscapeWithParser:
    def test_parse_then_escape_no_changes_for_clean_vars(self, parser, escaper, sample_env_content):
        vars = parser.parse(sample_env_content)
        result = escaper.process(vars)
        assert result.has_changes() is False

    def test_escape_then_unescape_roundtrip(self, escaper, unescaper):
        original = {
            "MSG": "Hello\nWorld",
            "DATA": "tab\there",
            "PATH": "/usr\\local",
        }
        escaped = escaper.process(original)
        assert escaped.has_changes() is True
        restored = unescaper.process(escaped.vars)
        assert restored.vars == original

    def test_parse_escape_export_pipeline(self, parser, escaper, exporter):
        content = 'MULTILINE=line1\nSIMPLE=ok\n'
        vars = parser.parse(content)
        escaped = escaper.process(vars)
        export_result = exporter.export(escaped.vars, fmt="dotenv")
        assert export_result.rendered is not None
        assert "SIMPLE" in export_result.rendered

    def test_selective_escape_leaves_others_intact(self, parser):
        selective = EnvEscaper(keys=["SECRET"])
        vars = {"SECRET": "my\nsecret", "NAME": "Alice\nBob"}
        result = selective.process(vars)
        assert result.vars["SECRET"] == "my\\nsecret"
        assert result.vars["NAME"] == "Alice\nBob"
