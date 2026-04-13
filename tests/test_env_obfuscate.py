import base64
import hashlib
import pytest
from envoy.env_obfuscate import EnvObfuscator, ObfuscateChange, ObfuscateResult


@pytest.fixture
def obfuscator():
    return EnvObfuscator()


@pytest.fixture
def sample_vars():
    return {"DB_PASS": "secret123", "API_KEY": "abc", "APP_NAME": "myapp"}


class TestObfuscateResult:
    def test_repr(self):
        r = ObfuscateResult(changes=[object()], skipped=["X"])
        assert "changed=1" in repr(r)
        assert "skipped=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = ObfuscateResult()
        assert r.has_changes is False

    def test_has_changes_true_when_populated(self):
        change = ObfuscateChange(key="K", original="v", obfuscated="x", method="hash")
        r = ObfuscateResult(changes=[change])
        assert r.has_changes is True


class TestObfuscateChange:
    def test_repr_contains_key_and_method(self):
        c = ObfuscateChange(key="MY_KEY", original="val", obfuscated="abc", method="base64")
        assert "MY_KEY" in repr(c)
        assert "base64" in repr(c)


class TestEnvObfuscator:
    def test_invalid_method_raises(self):
        with pytest.raises(ValueError, match="method must be one of"):
            EnvObfuscator(method="rot13")

    def test_hash_method_produces_fixed_length(self, sample_vars):
        ob = EnvObfuscator(method="hash", hash_length=8)
        result = ob.obfuscate(sample_vars)
        for change in result.changes:
            assert len(change.obfuscated) == 8

    def test_hash_is_sha256_based(self):
        ob = EnvObfuscator(method="hash", hash_length=64)
        result = ob.obfuscate({"K": "hello"})
        expected = hashlib.sha256(b"hello").hexdigest()
        assert result.vars["K"] == expected

    def test_base64_method_roundtrip(self):
        ob = EnvObfuscator(method="base64")
        result = ob.obfuscate({"SECRET": "my_value"})
        encoded = result.vars["SECRET"]
        decoded = base64.b64decode(encoded.encode()).decode()
        assert decoded == "my_value"

    def test_specific_keys_only_obfuscated(self, sample_vars):
        ob = EnvObfuscator(keys=["DB_PASS"], method="hash")
        result = ob.obfuscate(sample_vars)
        assert result.vars["APP_NAME"] == "myapp"
        assert result.vars["DB_PASS"] != "secret123"
        assert "APP_NAME" in result.skipped
        assert "API_KEY" in result.skipped

    def test_all_keys_obfuscated_when_none_specified(self, sample_vars):
        ob = EnvObfuscator(method="hash")
        result = ob.obfuscate(sample_vars)
        assert len(result.changes) == len(sample_vars)
        assert result.skipped == []

    def test_empty_vars_returns_empty_result(self):
        ob = EnvObfuscator()
        result = ob.obfuscate({})
        assert result.vars == {}
        assert result.has_changes is False

    def test_empty_value_obfuscated(self):
        ob = EnvObfuscator(method="base64")
        result = ob.obfuscate({"EMPTY": ""})
        assert result.vars["EMPTY"] == base64.b64encode(b"").decode()
