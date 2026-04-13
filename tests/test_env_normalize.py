"""Tests for EnvNormalizer."""
import pytest
from envoy.env_normalize import EnvNormalizer, NormalizeResult, NormalizeChange


@pytest.fixture
def normalizer():
    return EnvNormalizer()


@pytest.fixture
def no_quote_normalizer():
    return EnvNormalizer(strip_quotes=False)


class TestNormalizeResult:
    def test_repr(self):
        r = NormalizeResult()
        assert "NormalizeResult" in repr(r)
        assert "has_changes=False" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = NormalizeResult()
        assert r.has_changes is False

    def test_has_changes_true_when_populated(self):
        change = NormalizeChange(key="K", original="v ", normalized="v", reason="stripped whitespace")
        r = NormalizeResult(changes=[change], vars={"K": "v"})
        assert r.has_changes is True

    def test_changed_keys_returns_keys(self):
        change = NormalizeChange(key="FOO", original=" bar ", normalized="bar", reason="stripped whitespace")
        r = NormalizeResult(changes=[change], vars={"FOO": "bar"})
        assert r.changed_keys == ["FOO"]


class TestEnvNormalizer:
    def test_clean_value_unchanged(self, normalizer):
        result = normalizer.normalize({"KEY": "value"})
        assert not result.has_changes
        assert result.vars["KEY"] == "value"

    def test_strips_leading_trailing_whitespace(self, normalizer):
        result = normalizer.normalize({"KEY": "  hello  "})
        assert result.has_changes
        assert result.vars["KEY"] == "hello"

    def test_strips_double_quotes(self, normalizer):
        result = normalizer.normalize({"KEY": '"myvalue"'})
        assert result.has_changes
        assert result.vars["KEY"] == "myvalue"

    def test_strips_single_quotes(self, normalizer):
        result = normalizer.normalize({"KEY": "'myvalue'"})
        assert result.has_changes
        assert result.vars["KEY"] == "myvalue"

    def test_no_strip_quotes_leaves_quotes(self, no_quote_normalizer):
        result = no_quote_normalizer.normalize({"KEY": '"myvalue"'})
        assert not result.has_changes
        assert result.vars["KEY"] == '"myvalue"'

    def test_fixes_crlf_line_endings(self, normalizer):
        result = normalizer.normalize({"KEY": "line1\r\nline2"})
        assert result.has_changes
        assert "\r\n" not in result.vars["KEY"]
        assert result.vars["KEY"] == "line1\nline2"

    def test_multiple_changes_recorded(self, normalizer):
        vars_ = {"A": '  "hello"  ', "B": "clean", "C": " spaced "}
        result = normalizer.normalize(vars_)
        assert len(result.changes) == 2
        assert "B" not in result.changed_keys

    def test_reason_included_in_change(self, normalizer):
        result = normalizer.normalize({"KEY": "  val  "})
        assert result.has_changes
        assert result.changes[0].reason != ""

    def test_empty_vars_returns_empty_result(self, normalizer):
        result = normalizer.normalize({})
        assert not result.has_changes
        assert result.vars == {}

    def test_change_repr(self):
        c = NormalizeChange(key="X", original="old", normalized="new", reason="test")
        assert "NormalizeChange" in repr(c)
        assert "X" in repr(c)
