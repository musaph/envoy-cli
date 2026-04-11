"""Tests for envoy.env_format module."""
import pytest
from envoy.env_format import EnvFormatter, FormatChange, FormatResult


@pytest.fixture
def formatter():
    return EnvFormatter()


@pytest.fixture
def sample_vars():
    return {
        "db_host": "  localhost  ",
        "db_port": "5432",
        "api_key": "secret",
        "empty_var": "",
    }


class TestFormatResult:
    def test_repr(self):
        r = FormatResult(vars={}, changes=[], skipped=[])
        assert "FormatResult" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = FormatResult(vars={}, changes=[], skipped=[])
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        change = FormatChange("key", "old", "new", "reason")
        r = FormatResult(vars={}, changes=[change])
        assert r.has_changes


class TestFormatChangeRepr:
    def test_repr_contains_key_and_reason(self):
        c = FormatChange("MY_KEY", "old", "new", "key uppercased")
        assert "MY_KEY" in repr(c)
        assert "key uppercased" in repr(c)


class TestEnvFormatter:
    def test_uppercase_keys_by_default(self, formatter, sample_vars):
        result = formatter.format({"db_host": "localhost"})
        assert "DB_HOST" in result.vars
        assert "db_host" not in result.vars

    def test_strip_values_by_default(self, formatter):
        result = formatter.format({"KEY": "  value  "})
        assert result.vars["KEY"] == "value"

    def test_strip_records_change(self, formatter):
        result = formatter.format({"KEY": "  value  "})
        reasons = [c.reason for c in result.changes]
        assert any("normalized" in r for r in reasons)

    def test_no_uppercase_option(self):
        f = EnvFormatter(uppercase_keys=False)
        result = f.format({"db_host": "localhost"})
        assert "db_host" in result.vars

    def test_quote_values(self):
        f = EnvFormatter(quote_values=True)
        result = f.format({"KEY": "value"})
        assert result.vars["KEY"] == '"value"'

    def test_quote_skips_already_quoted(self):
        f = EnvFormatter(quote_values=True)
        result = f.format({"KEY": '"already"'})
        assert result.vars["KEY"] == '"already"'

    def test_remove_empty_skips_blank_vars(self):
        f = EnvFormatter(remove_empty=True)
        result = f.format({"KEY": "", "OTHER": "val"})
        assert "KEY" not in result.vars
        assert "KEY" in result.skipped

    def test_no_changes_on_clean_input(self):
        f = EnvFormatter(uppercase_keys=True, strip_values=True)
        result = f.format({"KEY": "value"})
        assert not result.has_changes
        assert result.vars["KEY"] == "value"

    def test_uppercase_change_recorded(self):
        result = EnvFormatter().format({"lower": "val"})
        keys_changed = [c.key for c in result.changes]
        assert "lower" in keys_changed

    def test_empty_input(self, formatter):
        result = formatter.format({})
        assert result.vars == {}
        assert not result.has_changes
