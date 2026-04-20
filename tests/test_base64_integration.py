"""Integration tests: Base64 processor with parser and exporter."""
import base64
import pytest
from envoy.env_base64 import EnvBase64Processor
from envoy.parser import EnvParser
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def processor():
    return EnvBase64Processor()


@pytest.fixture
def exporter():
    return EnvExporter()


@pytest.fixture
def sample_env_content():
    return "NAME=alice\nSECRET=hunter2\nAPI_KEY=supersecret\n"


class TestBase64WithParser:
    def test_parse_then_encode_roundtrip(self, parser, processor, sample_env_content):
        vars = parser.parse(sample_env_content)
        encoded_result = processor.encode(vars)
        decoded_result = processor.decode(encoded_result.vars)
        assert decoded_result.vars == vars

    def test_encode_produces_valid_base64(self, parser, processor, sample_env_content):
        vars = parser.parse(sample_env_content)
        result = processor.encode(vars)
        for key, value in result.vars.items():
            # Should not raise
            base64.b64decode(value.encode())

    def test_selective_encode_leaves_non_targeted_unchanged(self, parser, sample_env_content):
        selective = EnvBase64Processor(keys=["SECRET"])
        vars = parser.parse(sample_env_content)
        result = selective.encode(vars)
        assert result.vars["NAME"] == vars["NAME"]
        assert result.vars["API_KEY"] == vars["API_KEY"]
        assert result.vars["SECRET"] != vars["SECRET"]

    def test_export_after_encode(self, parser, processor, exporter, sample_env_content):
        vars = parser.parse(sample_env_content)
        encoded = processor.encode(vars)
        shell_output = exporter.export(encoded.vars, fmt="shell")
        assert shell_output.content
        for key in vars:
            assert key in shell_output.content
