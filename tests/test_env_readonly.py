"""Tests for envoy.env_readonly."""
import pytest
from envoy.env_readonly import EnvReadonlyGuard, ReadonlyResult, ReadonlyViolation


@pytest.fixture
def guard():
    return EnvReadonlyGuard(readonly_keys=["DATABASE_URL", "SECRET_KEY"])


@pytest.fixture
def sample_base():
    return {
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "s3cr3t",
        "DEBUG": "false",
    }


class TestReadonlyResult:
    def test_repr(self):
        r = ReadonlyResult(protected={"A": "1"}, violations=[], applied={"A": "1"})
        assert "ReadonlyResult" in repr(r)
        assert "protected=1" in repr(r)

    def test_is_clean_when_no_violations(self):
        r = ReadonlyResult()
        assert r.is_clean is True

    def test_is_not_clean_with_violations(self):
        v = ReadonlyViolation(key="X", old_value="a", new_value="b")
        r = ReadonlyResult(violations=[v])
        assert r.is_clean is False


class TestReadonlyViolation:
    def test_repr_contains_key_and_values(self):
        v = ReadonlyViolation(key="SECRET_KEY", old_value="old", new_value="new")
        text = repr(v)
        assert "SECRET_KEY" in text
        assert "old" in text
        assert "new" in text


class TestEnvReadonlyGuard:
    def test_no_changes_to_readonly_keys_is_clean(self, guard, sample_base):
        incoming = dict(sample_base)  # identical
        result = guard.enforce(sample_base, incoming)
        assert result.is_clean
        assert result.applied["DATABASE_URL"] == sample_base["DATABASE_URL"]

    def test_attempt_to_change_readonly_creates_violation(self, guard, sample_base):
        incoming = dict(sample_base)
        incoming["DATABASE_URL"] = "postgres://other/db"
        result = guard.enforce(sample_base, incoming)
        assert not result.is_clean
        assert len(result.violations) == 1
        assert result.violations[0].key == "DATABASE_URL"

    def test_readonly_value_preserved_in_applied(self, guard, sample_base):
        incoming = dict(sample_base)
        incoming["SECRET_KEY"] = "hacked"
        result = guard.enforce(sample_base, incoming)
        assert result.applied["SECRET_KEY"] == "s3cr3t"

    def test_non_readonly_key_updated_normally(self, guard, sample_base):
        incoming = dict(sample_base)
        incoming["DEBUG"] = "true"
        result = guard.enforce(sample_base, incoming)
        assert result.applied["DEBUG"] == "true"
        assert result.is_clean

    def test_new_key_in_incoming_added_freely(self, guard, sample_base):
        incoming = dict(sample_base)
        incoming["NEW_VAR"] = "hello"
        result = guard.enforce(sample_base, incoming)
        assert result.applied["NEW_VAR"] == "hello"

    def test_multiple_violations_detected(self, guard, sample_base):
        incoming = {"DATABASE_URL": "changed", "SECRET_KEY": "also_changed", "DEBUG": "true"}
        result = guard.enforce(sample_base, incoming)
        assert len(result.violations) == 2

    def test_list_readonly_returns_uppercased_keys(self, guard):
        keys = guard.list_readonly()
        assert "DATABASE_URL" in keys
        assert "SECRET_KEY" in keys

    def test_empty_readonly_list_allows_all_changes(self, sample_base):
        free_guard = EnvReadonlyGuard()
        incoming = {k: "changed" for k in sample_base}
        result = free_guard.enforce(sample_base, incoming)
        assert result.is_clean
        assert all(v == "changed" for v in result.applied.values())
