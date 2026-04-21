import base64
import pytest
from envoy.parser import EnvParser
from envoy.env_encode import EnvEncoder
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def encoder_url():
    return EnvEncoder(encoding="url")


@pytest.fixture
def encoder_b64():
    return EnvEncoder(encoding="base64")


@pytest.fixture
def sample_env_content():
    return "REDIRECT_URL=https://example.com/path?foo=bar&baz=qux\nPLAIN=hello\n"


class TestEncodeWithParser:
    def test_parse_then_url_encode(self, parser, encoder_url, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        result = encoder_url.encode(vars_)
        assert result.has_changes()
        assert "REDIRECT_URL" in result.changed_keys()

    def test_parse_then_b64_encode_roundtrip(self, parser, encoder_b64):
        content = "SECRET=mysecretvalue\n"
        vars_ = parser.parse(content)
        encoded = encoder_b64.apply(vars_)
        decoded_val = base64.b64decode(encoded["SECRET"].encode()).decode()
        assert decoded_val == "mysecretvalue"

    def test_selective_key_encoding(self, parser, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        enc = EnvEncoder(encoding="url", keys=["PLAIN"])
        result = enc.encode(vars_)
        # PLAIN=hello has no URL-unsafe chars, so no changes expected
        assert "REDIRECT_URL" not in result.changed_keys()

    def test_encode_then_serialize_roundtrip(self, parser, encoder_url):
        content = "A=hello world\nB=safe\n"
        vars_ = parser.parse(content)
        encoded = encoder_url.apply(vars_)
        serialized = parser.serialize(encoded)
        reparsed = parser.parse(serialized)
        assert reparsed["A"] == "hello%20world"
        assert reparsed["B"] == "safe"

    def test_hex_encoding_with_exporter(self, parser):
        content = "TOKEN=abc\n"
        vars_ = parser.parse(content)
        enc = EnvEncoder(encoding="hex")
        encoded = enc.apply(vars_)
        exporter = EnvExporter()
        export_result = exporter.export(encoded, fmt="shell")
        assert "616263" in export_result.render()
