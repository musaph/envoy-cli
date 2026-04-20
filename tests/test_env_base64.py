"""Tests for envoy/env_base64.py."""
import base64
import pytest
from envoy.env_base64 import Base64Change, Base64Result, EnvBase64Processor


@pytest.fixture
def processor():
    return EnvBase64Processor()


@pytest.fixture
def selective():
    return EnvBase64Processor(keys=["SECRET", "TOKEN"])


@pytest.fixture
def sample_vars():
    return {"NAME": "alice", "SECRET": "hunter2", "TOKEN": "abc123"}


class TestBase64Result:
    def test_repr(self):
        r = Base64Result()
        assert "Base64Result" in repr(r)

    def test_has_changes_false_when_empty(self):
        assert Base64Result().has_changes() is False

    def test_has_changes_true_when_populated(self):
        c = Base64Change(key="K", original="v", result="dg==", operation="encode")
        r = Base64Result(changes=[c], vars={"K": "dg=="})
        assert r.has_changes() is True

    def test_has_errors_false_when_no_errors(self):
        c = Base64Change(key="K", original="v", result="dg==", operation="encode")
        r = Base64Result(changes=[c])
        assert r.has_errors() is False

    def test_has_errors_true_when_error_present(self):
        c = Base64Change(key="K", original="bad", result="bad", operation="decode", error="Invalid")
        r = Base64Result(changes=[c])
        assert r.has_errors() is True

    def test_changed_keys_excludes_errors(self):
        ok = Base64Change(key="A", original="x", result="eA==", operation="encode")
        bad = Base64Change(key="B", original="!", result="!", operation="decode", error="oops")
        r = Base64Result(changes=[ok, bad])
        assert r.changed_keys() == ["A"]
        assert r.error_keys() == ["B"]


class TestEnvBase64Processor:
    def test_encode_all_keys(self, processor, sample_vars):
        result = processor.encode(sample_vars)
        for key, value in sample_vars.items():
            expected = base64.b64encode(value.encode()).decode()
            assert result.vars[key] == expected

    def test_encode_returns_correct_change_count(self, processor, sample_vars):
        result = processor.encode(sample_vars)
        assert len(result.changes) == len(sample_vars)

    def test_decode_reverses_encode(self, processor, sample_vars):
        encoded = processor.encode(sample_vars)
        decoded = processor.decode(encoded.vars)
        assert decoded.vars == sample_vars

    def test_selective_encode_only_specified_keys(self, selective, sample_vars):
        result = selective.encode(sample_vars)
        assert result.vars["NAME"] == sample_vars["NAME"]  # unchanged
        assert result.vars["SECRET"] != sample_vars["SECRET"]
        assert result.vars["TOKEN"] != sample_vars["TOKEN"]
        assert len(result.changes) == 2

    def test_decode_invalid_value_records_error(self, processor):
        vars = {"BAD": "not-valid-base64!!!"}
        result = processor.decode(vars)
        assert result.has_errors()
        assert "BAD" in result.error_keys()
        assert result.vars["BAD"] == "not-valid-base64!!!"  # unchanged on error

    def test_encode_empty_value(self, processor):
        result = processor.encode({"EMPTY": ""})
        assert result.vars["EMPTY"] == base64.b64encode(b"").decode()
        assert result.has_changes()

    def test_decode_empty_encoded_value(self, processor):
        encoded_empty = base64.b64encode(b"").decode()
        result = processor.decode({"EMPTY": encoded_empty})
        assert result.vars["EMPTY"] == ""
        assert not result.has_errors()

    def test_change_repr_no_error(self):
        c = Base64Change(key="K", original="v", result="dg==", operation="encode")
        assert "encode" in repr(c)
        assert "error" not in repr(c)

    def test_change_repr_with_error(self):
        c = Base64Change(key="K", original="bad", result="bad", operation="decode", error="Invalid")
        assert "error" in repr(c)
