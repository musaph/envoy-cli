"""Tests for EnvTruncator."""
import pytest
from envoy.env_truncate import EnvTruncator, TruncateResult, TruncateChange


@pytest.fixture
def truncator():
    return EnvTruncator(max_length=10, suffix="...")


@pytest.fixture
def sample_vars():
    return {
        "SHORT": "hi",
        "LONG": "this_is_a_very_long_value",
        "EXACT": "1234567890",
        "OVER": "12345678901",
    }


class TestTruncateResult:
    def test_repr(self):
        r = TruncateResult()
        assert "TruncateResult" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = TruncateResult()
        assert r.has_changes is False

    def test_has_changes_true_when_populated(self):
        c = TruncateChange("K", "long_val", "lo...", 8, 5)
        r = TruncateResult(changes=[c])
        assert r.has_changes is True


class TestTruncateChange:
    def test_repr_contains_key(self):
        c = TruncateChange("MY_KEY", "abcdefghij", "abc...", 10, 6)
        assert "MY_KEY" in repr(c)
        assert "10" in repr(c)


class TestEnvTruncator:
    def test_no_truncation_for_short_values(self, truncator, sample_vars):
        result = truncator.truncate({"SHORT": "hi"})
        assert not result.has_changes

    def test_exact_length_not_truncated(self, truncator):
        result = truncator.truncate({"EXACT": "1234567890"})
        assert not result.has_changes

    def test_over_length_is_truncated(self, truncator):
        result = truncator.truncate({"OVER": "12345678901"})
        assert result.has_changes
        assert len(result.changes) == 1
        assert result.changes[0].key == "OVER"

    def test_truncated_value_ends_with_suffix(self, truncator):
        result = truncator.truncate({"LONG": "this_is_a_very_long_value"})
        change = result.changes[0]
        assert change.truncated.endswith("...")

    def test_truncated_length_respects_max(self, truncator):
        result = truncator.truncate({"LONG": "this_is_a_very_long_value"})
        change = result.changes[0]
        assert len(change.truncated) == truncator.max_length

    def test_skip_keys_excluded(self, truncator):
        t = EnvTruncator(max_length=5, suffix="...", skip_keys=["SECRET"])
        result = t.truncate({"SECRET": "this_is_long", "OTHER": "this_is_long"})
        keys_changed = [c.key for c in result.changes]
        assert "SECRET" not in keys_changed
        assert "OTHER" in keys_changed
        assert "SECRET" in result.skipped

    def test_apply_returns_updated_dict(self, truncator):
        vars_ = {"SHORT": "hi", "LONG": "this_is_a_very_long_value"}
        out = truncator.apply(vars_)
        assert out["SHORT"] == "hi"
        assert len(out["LONG"]) == truncator.max_length

    def test_apply_does_not_mutate_original(self, truncator):
        vars_ = {"LONG": "this_is_a_very_long_value"}
        original_val = vars_["LONG"]
        truncator.apply(vars_)
        assert vars_["LONG"] == original_val

    def test_invalid_max_length_raises(self):
        with pytest.raises(ValueError):
            EnvTruncator(max_length=0)

    def test_multiple_long_values(self, truncator, sample_vars):
        result = truncator.truncate(sample_vars)
        changed_keys = {c.key for c in result.changes}
        assert "LONG" in changed_keys
        assert "OVER" in changed_keys
        assert "SHORT" not in changed_keys
        assert "EXACT" not in changed_keys
