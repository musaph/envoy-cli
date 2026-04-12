"""Tests for envoy.env_required."""
import pytest
from envoy.env_required import EnvRequiredChecker, RequiredResult, RequiredViolation


@pytest.fixture
def checker():
    return EnvRequiredChecker(required_keys=["DB_HOST", "DB_PORT", "API_KEY"])


@pytest.fixture
def allow_empty_checker():
    return EnvRequiredChecker(
        required_keys=["DB_HOST", "API_KEY"], allow_empty=True
    )


class TestRequiredViolation:
    def test_repr_contains_key_and_reason(self):
        v = RequiredViolation(key="FOO", reason="key not present")
        assert "FOO" in repr(v)
        assert "key not present" in repr(v)


class TestRequiredResult:
    def test_repr(self):
        r = RequiredResult()
        assert "missing=0" in repr(r)
        assert "satisfied=True" in repr(r)

    def test_is_satisfied_when_no_violations(self):
        r = RequiredResult()
        assert r.is_satisfied is True

    def test_is_not_satisfied_with_missing(self):
        r = RequiredResult(missing=[RequiredViolation("X", "key not present")])
        assert r.is_satisfied is False

    def test_is_not_satisfied_with_empty(self):
        r = RequiredResult(empty=[RequiredViolation("X", "value is empty")])
        assert r.is_satisfied is False

    def test_violations_combines_missing_and_empty(self):
        r = RequiredResult(
            missing=[RequiredViolation("A", "key not present")],
            empty=[RequiredViolation("B", "value is empty")],
        )
        assert len(r.violations) == 2


class TestEnvRequiredChecker:
    def test_all_present_and_non_empty(self, checker):
        vars_ = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"}
        result = checker.check(vars_)
        assert result.is_satisfied

    def test_missing_key_reported(self, checker):
        vars_ = {"DB_HOST": "localhost", "DB_PORT": "5432"}
        result = checker.check(vars_)
        assert not result.is_satisfied
        assert any(v.key == "API_KEY" for v in result.missing)

    def test_empty_value_reported(self, checker):
        vars_ = {"DB_HOST": "localhost", "DB_PORT": "", "API_KEY": "x"}
        result = checker.check(vars_)
        assert not result.is_satisfied
        assert any(v.key == "DB_PORT" for v in result.empty)

    def test_whitespace_only_treated_as_empty(self, checker):
        vars_ = {"DB_HOST": "h", "DB_PORT": "   ", "API_KEY": "k"}
        result = checker.check(vars_)
        assert len(result.empty) == 1

    def test_allow_empty_skips_empty_check(self, allow_empty_checker):
        vars_ = {"DB_HOST": "", "API_KEY": ""}
        result = allow_empty_checker.check(vars_)
        assert result.is_satisfied

    def test_missing_keys_helper(self, checker):
        vars_ = {"DB_HOST": "h"}
        missing = checker.missing_keys(vars_)
        assert "DB_PORT" in missing
        assert "API_KEY" in missing
        assert "DB_HOST" not in missing

    def test_empty_keys_helper(self, checker):
        vars_ = {"DB_HOST": "h", "DB_PORT": "", "API_KEY": "k"}
        empty = checker.empty_keys(vars_)
        assert empty == ["DB_PORT"]

    def test_empty_keys_returns_empty_when_allow_empty(self, allow_empty_checker):
        vars_ = {"DB_HOST": "", "API_KEY": ""}
        assert allow_empty_checker.empty_keys(vars_) == []
