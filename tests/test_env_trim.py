"""Tests for envoy.env_trim module."""
import pytest
from envoy.env_trim import EnvTrimmer, TrimResult


@pytest.fixture
def trimmer() -> EnvTrimmer:
    return EnvTrimmer()


@pytest.fixture
def quote_trimmer() -> EnvTrimmer:
    return EnvTrimmer(strip_quotes=True)


class TestTrimResult:
    def test_repr(self):
        r = TrimResult(trimmed={"A": "1"}, changed_keys=["A"], skipped_keys=[])
        assert "changed=1" in repr(r)
        assert "skipped=0" in repr(r)
        assert "total=1" in repr(r)

    def test_has_changes_true(self):
        r = TrimResult(trimmed={}, changed_keys=["X"], skipped_keys=[])
        assert r.has_changes is True

    def test_has_changes_false(self):
        r = TrimResult(trimmed={}, changed_keys=[], skipped_keys=[])
        assert r.has_changes is False


class TestEnvTrimmer:
    def test_trims_leading_trailing_whitespace(self, trimmer):
        result = trimmer.trim({"KEY": "  hello  "})
        assert result.trimmed["KEY"] == "hello"
        assert "KEY" in result.changed_keys

    def test_no_change_when_already_clean(self, trimmer):
        result = trimmer.trim({"KEY": "hello"})
        assert result.trimmed["KEY"] == "hello"
        assert result.changed_keys == []

    def test_multiple_keys(self, trimmer):
        vars = {"A": " foo ", "B": "bar", "C": "\tbaz\n"}
        result = trimmer.trim(vars)
        assert result.trimmed["A"] == "foo"
        assert result.trimmed["B"] == "bar"
        assert result.trimmed["C"] == "baz"
        assert set(result.changed_keys) == {"A", "C"}

    def test_skip_keys_are_preserved_unchanged(self):
        t = EnvTrimmer(skip_keys=["SECRET"])
        result = t.trim({"SECRET": "  raw  ", "OTHER": "  val  "})
        assert result.trimmed["SECRET"] == "  raw  "
        assert result.trimmed["OTHER"] == "val"
        assert "SECRET" in result.skipped_keys
        assert "SECRET" not in result.changed_keys

    def test_strip_double_quotes(self, quote_trimmer):
        result = quote_trimmer.trim({"KEY": '"hello"'})
        assert result.trimmed["KEY"] == "hello"
        assert "KEY" in result.changed_keys

    def test_strip_single_quotes(self, quote_trimmer):
        result = quote_trimmer.trim({"KEY": "'world'"})
        assert result.trimmed["KEY"] == "world"

    def test_no_strip_quotes_when_disabled(self, trimmer):
        result = trimmer.trim({"KEY": '"hello"'})
        assert result.trimmed["KEY"] == '"hello"'

    def test_mismatched_quotes_not_stripped(self, quote_trimmer):
        result = quote_trimmer.trim({"KEY": '"hello\''})
        assert result.trimmed["KEY"] == '"hello\''

    def test_empty_vars_returns_empty_result(self, trimmer):
        result = trimmer.trim({})
        assert result.trimmed == {}
        assert result.changed_keys == []
        assert result.has_changes is False

    def test_whitespace_only_value_becomes_empty(self, trimmer):
        result = trimmer.trim({"BLANK": "   "})
        assert result.trimmed["BLANK"] == ""
        assert "BLANK" in result.changed_keys
