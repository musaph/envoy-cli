"""Tests for EnvCoercer."""
import pytest
from envoy.env_coerce import CoerceChange, CoerceResult, EnvCoercer


@pytest.fixture
def coercer():
    return EnvCoercer(rules=["strip"])


@pytest.fixture
def multi_coercer():
    return EnvCoercer(rules=["strip", "uppercase"])


class TestCoerceResult:
    def test_repr(self):
        r = CoerceResult(changes=[CoerceChange("K", "v", "V", "uppercase")])
        assert "CoerceResult" in repr(r)
        assert "1" in repr(r)

    def test_has_changes_false_when_empty(self):
        assert CoerceResult().has_changes is False

    def test_has_changes_true_when_populated(self):
        r = CoerceResult(changes=[CoerceChange("K", "a", "b", "strip")])
        assert r.has_changes is True


class TestEnvCoercer:
    def test_unknown_rule_raises(self):
        with pytest.raises(ValueError, match="Unknown coercion rules"):
            EnvCoercer(rules=["nonexistent"])

    def test_strip_removes_whitespace(self, coercer):
        result = coercer.coerce({"KEY": "  hello  "})
        assert result.has_changes
        assert result.changes[0].coerced == "hello"
        assert result.changes[0].rule == "strip"

    def test_no_change_when_already_clean(self, coercer):
        result = coercer.coerce({"KEY": "hello"})
        assert not result.has_changes

    def test_uppercase_rule(self):
        c = EnvCoercer(rules=["uppercase"])
        result = c.coerce({"KEY": "hello"})
        assert result.changes[0].coerced == "HELLO"

    def test_lowercase_rule(self):
        c = EnvCoercer(rules=["lowercase"])
        result = c.coerce({"KEY": "HELLO"})
        assert result.changes[0].coerced == "hello"

    def test_bool_normalize_true_variants(self):
        c = EnvCoercer(rules=["bool_normalize"])
        for val in ("1", "yes", "YES", "true", "True", "on", "ON"):
            result = c.coerce({"FLAG": val})
            assert result.changes[0].coerced == "true", f"Failed for {val!r}"

    def test_bool_normalize_false_variants(self):
        c = EnvCoercer(rules=["bool_normalize"])
        for val in ("0", "no", "NO", "false", "False", "off", "OFF"):
            result = c.coerce({"FLAG": val})
            assert result.changes[0].coerced == "false", f"Failed for {val!r}"

    def test_bool_normalize_passthrough(self):
        c = EnvCoercer(rules=["bool_normalize"])
        result = c.coerce({"FLAG": "maybe"})
        assert not result.has_changes

    def test_strip_quotes_double(self):
        c = EnvCoercer(rules=["strip_quotes"])
        result = c.coerce({"KEY": '"hello"'})
        assert result.changes[0].coerced == "hello"

    def test_strip_quotes_single(self):
        c = EnvCoercer(rules=["strip_quotes"])
        result = c.coerce({"KEY": "'hello'"})
        assert result.changes[0].coerced == "hello"

    def test_strip_quotes_no_change_when_unquoted(self):
        c = EnvCoercer(rules=["strip_quotes"])
        result = c.coerce({"KEY": "hello"})
        assert not result.has_changes

    def test_multiple_rules_applied_in_order(self, multi_coercer):
        result = multi_coercer.coerce({"KEY": "  hello  "})
        assert result.has_changes
        assert result.changes[0].coerced == "HELLO"

    def test_coerce_value_direct(self):
        c = EnvCoercer(rules=["strip", "uppercase"])
        assert c.coerce_value("  world  ") == "WORLD"

    def test_multiple_keys(self, coercer):
        result = coercer.coerce({"A": "  a  ", "B": "b", "C": "  c"})
        keys_changed = {ch.key for ch in result.changes}
        assert "A" in keys_changed
        assert "B" not in keys_changed
        assert "C" in keys_changed
