"""Tests for envoy/env_protect.py."""
import pytest
from envoy.env_protect import EnvProtector, ProtectResult, ProtectViolation


@pytest.fixture
def protector() -> EnvProtector:
    return EnvProtector(protected_keys=["DATABASE_URL", "SECRET_KEY"])


@pytest.fixture
def sample_vars() -> dict:
    return {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "s3cr3t", "DEBUG": "true"}


class TestProtectViolation:
    def test_repr_contains_key_and_reason(self):
        v = ProtectViolation(key="FOO", reason="deletion of protected key")
        assert "FOO" in repr(v)
        assert "deletion" in repr(v)


class TestProtectResult:
    def test_repr(self):
        r = ProtectResult(protected_keys={"A"}, violations=[])
        assert "ProtectResult" in repr(r)

    def test_is_clean_when_no_violations(self):
        r = ProtectResult(protected_keys={"A"}, violations=[])
        assert r.is_clean is True

    def test_is_not_clean_with_violations(self):
        v = ProtectViolation(key="A", reason="test")
        r = ProtectResult(protected_keys={"A"}, violations=[v])
        assert r.is_clean is False

    def test_violation_keys_returns_list(self):
        v = ProtectViolation(key="DB", reason="deletion of protected key")
        r = ProtectResult(protected_keys={"DB"}, violations=[v])
        assert r.violation_keys == ["DB"]


class TestEnvProtector:
    def test_protected_keys_property(self, protector):
        assert "DATABASE_URL" in protector.protected_keys
        assert "SECRET_KEY" in protector.protected_keys

    def test_check_delete_no_violation(self, protector):
        result = protector.check_delete(["DEBUG", "PORT"])
        assert result.is_clean

    def test_check_delete_with_violation(self, protector):
        result = protector.check_delete(["DATABASE_URL", "DEBUG"])
        assert not result.is_clean
        assert "DATABASE_URL" in result.violation_keys

    def test_check_delete_all_protected(self, protector):
        result = protector.check_delete(["DATABASE_URL", "SECRET_KEY"])
        assert len(result.violations) == 2

    def test_check_overwrite_no_violation(self, protector, sample_vars):
        proposed = dict(sample_vars)  # same values
        result = protector.check_overwrite(sample_vars, proposed)
        assert result.is_clean

    def test_check_overwrite_with_violation(self, protector, sample_vars):
        proposed = dict(sample_vars)
        proposed["DATABASE_URL"] = "postgres://newhost/db"
        result = protector.check_overwrite(sample_vars, proposed)
        assert not result.is_clean
        assert "DATABASE_URL" in result.violation_keys

    def test_check_overwrite_new_key_not_violation(self, protector, sample_vars):
        proposed = dict(sample_vars)
        proposed["NEW_KEY"] = "value"
        result = protector.check_overwrite(sample_vars, proposed)
        assert result.is_clean

    def test_filter_safe_restores_protected(self, protector, sample_vars):
        proposed = {"DATABASE_URL": "changed", "SECRET_KEY": "changed", "DEBUG": "false"}
        safe = protector.filter_safe(proposed, sample_vars)
        assert safe["DATABASE_URL"] == sample_vars["DATABASE_URL"]
        assert safe["SECRET_KEY"] == sample_vars["SECRET_KEY"]
        assert safe["DEBUG"] == "false"

    def test_filter_safe_allows_new_unprotected_keys(self, protector, sample_vars):
        proposed = dict(sample_vars)
        proposed["NEW_VAR"] = "hello"
        safe = protector.filter_safe(proposed, sample_vars)
        assert safe["NEW_VAR"] == "hello"

    def test_empty_protector_never_violates(self):
        p = EnvProtector([])
        result = p.check_delete(["ANY_KEY"])
        assert result.is_clean
        result2 = p.check_overwrite({"X": "a"}, {"X": "b"})
        assert result2.is_clean
