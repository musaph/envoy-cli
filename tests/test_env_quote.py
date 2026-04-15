"""Tests for envoy.env_quote."""
import pytest
from envoy.env_quote import EnvQuoter, QuoteChange, QuoteResult


@pytest.fixture
def quoter():
    return EnvQuoter(style="double")


@pytest.fixture
def single_quoter():
    return EnvQuoter(style="single")


@pytest.fixture
def smart_quoter():
    return EnvQuoter(style="double", only_if_needed=True)


@pytest.fixture
def sample_vars():
    return {
        "HOST": "localhost",
        "DSN": "postgres://user:pass@host/db",
        "GREETING": "hello world",
        "EMPTY": "",
    }


# ---------------------------------------------------------------------------
# QuoteResult
# ---------------------------------------------------------------------------
class TestQuoteResult:
    def test_repr(self):
        r = QuoteResult(vars={"A": "1"}, changes=[])
        assert "QuoteResult" in repr(r)
        assert "total=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = QuoteResult(vars={}, changes=[])
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = QuoteResult(
            vars={},
            changes=[QuoteChange("K", "v", '"v"', "quoted")],
        )
        assert r.has_changes

    def test_changed_keys(self):
        r = QuoteResult(
            vars={},
            changes=[QuoteChange("FOO", "bar", '"bar"', "quoted")],
        )
        assert r.changed_keys == ["FOO"]


# ---------------------------------------------------------------------------
# EnvQuoter — construction
# ---------------------------------------------------------------------------
class TestEnvQuoterConstruction:
    def test_invalid_style_raises(self):
        with pytest.raises(ValueError, match="style"):
            EnvQuoter(style="backtick")

    def test_double_style_accepted(self):
        q = EnvQuoter(style="double")
        assert q._q == '"'

    def test_single_style_accepted(self):
        q = EnvQuoter(style="single")
        assert q._q == "'"


# ---------------------------------------------------------------------------
# EnvQuoter.quote
# ---------------------------------------------------------------------------
class TestEnvQuoterQuote:
    def test_plain_value_gets_double_quotes(self, quoter):
        result = quoter.quote({"KEY": "value"})
        assert result.vars["KEY"] == '"value"'

    def test_already_double_quoted_no_change(self, quoter):
        result = quoter.quote({"KEY": '"value"'})
        assert result.vars["KEY"] == '"value"'
        assert not result.has_changes

    def test_single_quoted_gets_requoted_to_double(self, quoter):
        result = quoter.quote({"KEY": "'value'"})
        assert result.vars["KEY"] == '"value"'
        change = result.changes[0]
        assert change.action == "requoted"

    def test_single_quoter_wraps_in_single_quotes(self, single_quoter):
        result = single_quoter.quote({"KEY": "hello"})
        assert result.vars["KEY"] == "'hello'"

    def test_empty_value_gets_quoted(self, quoter):
        result = quoter.quote({"KEY": ""})
        assert result.vars["KEY"] == '""'
        assert result.has_changes

    def test_smart_quoter_skips_simple_values(self, smart_quoter):
        result = smart_quoter.quote({"KEY": "simple"})
        assert result.vars["KEY"] == "simple"
        assert not result.has_changes

    def test_smart_quoter_quotes_value_with_space(self, smart_quoter):
        result = smart_quoter.quote({"KEY": "hello world"})
        assert result.vars["KEY"] == '"hello world"'
        assert result.has_changes

    def test_smart_quoter_quotes_empty_value(self, smart_quoter):
        result = smart_quoter.quote({"KEY": ""})
        assert result.vars["KEY"] == '""'


# ---------------------------------------------------------------------------
# EnvQuoter.unquote
# ---------------------------------------------------------------------------
class TestEnvQuoterUnquote:
    def test_removes_double_quotes(self, quoter):
        result = quoter.unquote({"KEY": '"value"'})
        assert result.vars["KEY"] == "value"
        assert result.has_changes

    def test_removes_single_quotes(self, quoter):
        result = quoter.unquote({"KEY": "'value'"})
        assert result.vars["KEY"] == "value"
        assert result.has_changes

    def test_unquoted_value_unchanged(self, quoter):
        result = quoter.unquote({"KEY": "value"})
        assert result.vars["KEY"] == "value"
        assert not result.has_changes

    def test_unquote_action_label(self, quoter):
        result = quoter.unquote({"KEY": '"val"'})
        assert result.changes[0].action == "unquoted"

    def test_multiple_vars(self, quoter, sample_vars):
        quoted = quoter.quote(sample_vars)
        unquoted = quoter.unquote(quoted.vars)
        # All values should be back to raw form
        for key, val in unquoted.vars.items():
            assert not (val.startswith('"') and val.endswith('"'))
