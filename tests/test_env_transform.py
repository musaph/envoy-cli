"""Tests for envoy.env_transform."""
import pytest
from envoy.env_transform import (
    EnvTransformer,
    TransformChange,
    TransformResult,
    BUILTIN_TRANSFORMS,
)


@pytest.fixture
def transformer():
    return EnvTransformer()


@pytest.fixture
def sample_vars():
    return {
        "APP_NAME": "myapp",
        "DEBUG": "True",
        "API_URL": "  https://example.com  ",
        "TOKEN": "'secret123'",
    }


class TestTransformResult:
    def test_repr(self):
        r = TransformResult(vars={}, changes=[TransformChange("K", "a", "A")], errors=[])
        assert "changes=1" in repr(r)
        assert "errors=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = TransformResult(vars={})
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = TransformResult(vars={}, changes=[TransformChange("K", "a", "A")])
        assert r.has_changes

    def test_has_errors_false_by_default(self):
        r = TransformResult(vars={})
        assert not r.has_errors

    def test_has_errors_true_when_populated(self):
        r = TransformResult(vars={}, errors=["oops"])
        assert r.has_errors


class TestEnvTransformer:
    def test_available_includes_builtins(self, transformer):
        names = transformer.available()
        for name in BUILTIN_TRANSFORMS:
            assert name in names

    def test_available_is_sorted(self, transformer):
        names = transformer.available()
        assert names == sorted(names)

    def test_upper_transform(self, transformer, sample_vars):
        result = transformer.transform({"APP_NAME": "myapp"}, "upper")
        assert result.vars["APP_NAME"] == "MYAPP"
        assert result.has_changes

    def test_lower_transform(self, transformer):
        result = transformer.transform({"KEY": "HELLO"}, "lower")
        assert result.vars["KEY"] == "hello"

    def test_strip_transform(self, transformer, sample_vars):
        result = transformer.transform({"API_URL": "  hello  "}, "strip")
        assert result.vars["API_URL"] == "hello"

    def test_trim_quotes_transform(self, transformer):
        result = transformer.transform({"TOKEN": "'secret'", "OTHER": '"value"'}, "trim_quotes")
        assert result.vars["TOKEN"] == "secret"
        assert result.vars["OTHER"] == "value"

    def test_to_bool_true_variants(self, transformer):
        for val in ("1", "yes", "on", "true", "True", "YES"):
            r = transformer.transform({"FLAG": val}, "to_bool")
            assert r.vars["FLAG"] == "true", f"Expected 'true' for input {val!r}"

    def test_to_bool_false_variants(self, transformer):
        for val in ("0", "no", "off", "false", "False"):
            r = transformer.transform({"FLAG": val}, "to_bool")
            assert r.vars["FLAG"] == "false"

    def test_no_change_when_already_transformed(self, transformer):
        result = transformer.transform({"KEY": "HELLO"}, "upper")
        assert not result.has_changes

    def test_limit_to_specific_keys(self, transformer, sample_vars):
        result = transformer.transform(sample_vars, "upper", keys=["APP_NAME"])
        assert result.vars["APP_NAME"] == "MYAPP"
        assert result.vars["DEBUG"] == sample_vars["DEBUG"]

    def test_unknown_transform_returns_error(self, transformer):
        result = transformer.transform({"K": "v"}, "nonexistent")
        assert result.has_errors
        assert not result.has_changes

    def test_missing_key_in_keys_list_adds_error(self, transformer):
        result = transformer.transform({"A": "hello"}, "upper", keys=["A", "MISSING"])
        assert result.has_errors
        assert any("MISSING" in e for e in result.errors)
        assert result.vars["A"] == "HELLO"

    def test_custom_transform_registered(self):
        t = EnvTransformer(custom={"reverse": lambda v: v[::-1]})
        result = t.transform({"KEY": "abc"}, "reverse")
        assert result.vars["KEY"] == "cba"
