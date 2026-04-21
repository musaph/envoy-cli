import pytest
from envoy.env_encode import EnvEncoder, EncodeChange, EncodeResult, SUPPORTED_ENCODINGS


@pytest.fixture
def url_encoder():
    return EnvEncoder(encoding="url")


@pytest.fixture
def b64_encoder():
    return EnvEncoder(encoding="base64")


@pytest.fixture
def hex_encoder():
    return EnvEncoder(encoding="hex")


@pytest.fixture
def sample_vars():
    return {
        "PLAIN": "hello",
        "URL_UNSAFE": "hello world/foo?bar=1",
        "ALREADY_SAFE": "safe",
    }


class TestEncodeResult:
    def test_repr(self):
        r = EncodeResult()
        assert "EncodeResult" in repr(r)

    def test_has_changes_false_when_empty(self):
        assert not EncodeResult().has_changes()

    def test_has_changes_true_when_populated(self):
        r = EncodeResult(changes=[EncodeChange("K", "v", "e", "url")])
        assert r.has_changes()

    def test_has_errors_false_when_empty(self):
        assert not EncodeResult().has_errors()

    def test_changed_keys(self):
        r = EncodeResult(changes=[EncodeChange("K", "v", "e", "url")])
        assert r.changed_keys() == ["K"]


class TestEnvEncoderUrl:
    def test_url_encodes_spaces(self, url_encoder, sample_vars):
        result = url_encoder.encode(sample_vars)
        keys = result.changed_keys()
        assert "URL_UNSAFE" in keys

    def test_plain_value_unchanged(self, url_encoder):
        result = url_encoder.encode({"A": "hello"})
        assert not result.has_changes()

    def test_apply_returns_encoded_dict(self, url_encoder):
        out = url_encoder.apply({"K": "a b"})
        assert out["K"] == "a%20b"

    def test_selective_keys_only_encodes_specified(self):
        enc = EnvEncoder(encoding="url", keys=["A"])
        out = enc.apply({"A": "a b", "B": "c d"})
        assert out["A"] == "a%20b"
        assert out["B"] == "c d"


class TestEnvEncoderBase64:
    def test_b64_encodes_value(self, b64_encoder):
        out = b64_encoder.apply({"K": "hello"})
        import base64
        assert out["K"] == base64.b64encode(b"hello").decode()

    def test_b64_empty_string(self, b64_encoder):
        out = b64_encoder.apply({"K": ""})
        assert out["K"] == ""


class TestEnvEncoderHex:
    def test_hex_encodes_value(self, hex_encoder):
        out = hex_encoder.apply({"K": "hi"})
        assert out["K"] == "6869"


class TestEnvEncoderValidation:
    def test_invalid_encoding_raises(self):
        with pytest.raises(ValueError, match="Unsupported encoding"):
            EnvEncoder(encoding="rot13")

    def test_all_supported_encodings_accepted(self):
        for enc in SUPPORTED_ENCODINGS:
            EnvEncoder(encoding=enc)
