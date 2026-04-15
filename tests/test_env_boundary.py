"""Tests for EnvBoundaryChecker."""
import pytest
from envoy.env_boundary import BoundaryRule, BoundaryViolation, BoundaryResult, EnvBoundaryChecker


@pytest.fixture
def checker():
    return EnvBoundaryChecker()


@pytest.fixture
def sample_vars():
    return {
        "SHORT": "hi",
        "LONG": "a" * 200,
        "PORT": "8080",
        "RATIO": "1.5",
        "NAME": "alice",
    }


class TestBoundaryResult:
    def test_repr(self):
        r = BoundaryResult()
        assert "BoundaryResult" in repr(r)
        assert "is_clean=True" in repr(r)

    def test_is_clean_when_no_violations(self):
        assert BoundaryResult().is_clean is True

    def test_is_not_clean_with_violation(self):
        v = BoundaryViolation(key="X", value="y", reason="too short")
        r = BoundaryResult(violations=[v])
        assert r.is_clean is False

    def test_violation_keys(self):
        v1 = BoundaryViolation(key="A", value="", reason="r")
        v2 = BoundaryViolation(key="B", value="", reason="r")
        r = BoundaryResult(violations=[v1, v2])
        assert r.violation_keys == ["A", "B"]


class TestEnvBoundaryChecker:
    def test_no_rules_no_violations(self, checker, sample_vars):
        result = checker.check(sample_vars)
        assert result.is_clean

    def test_min_length_passes(self, checker):
        checker.add_rule("NAME", BoundaryRule(min_length=3))
        result = checker.check({"NAME": "alice"})
        assert result.is_clean

    def test_min_length_violation(self, checker):
        checker.add_rule("NAME", BoundaryRule(min_length=10))
        result = checker.check({"NAME": "hi"})
        assert not result.is_clean
        assert result.violation_keys == ["NAME"]
        assert "min_length" in result.violations[0].reason

    def test_max_length_passes(self, checker):
        checker.add_rule("TOKEN", BoundaryRule(max_length=50))
        result = checker.check({"TOKEN": "abc123"})
        assert result.is_clean

    def test_max_length_violation(self, checker):
        checker.add_rule("TOKEN", BoundaryRule(max_length=5))
        result = checker.check({"TOKEN": "toolongvalue"})
        assert not result.is_clean
        assert "max_length" in result.violations[0].reason

    def test_numeric_min_passes(self, checker):
        checker.add_rule("PORT", BoundaryRule(min_value=1024))
        result = checker.check({"PORT": "8080"})
        assert result.is_clean

    def test_numeric_min_violation(self, checker):
        checker.add_rule("PORT", BoundaryRule(min_value=1024))
        result = checker.check({"PORT": "80"})
        assert not result.is_clean
        assert "min_value" in result.violations[0].reason

    def test_numeric_max_violation(self, checker):
        checker.add_rule("RATIO", BoundaryRule(max_value=1.0))
        result = checker.check({"RATIO": "2.5"})
        assert not result.is_clean
        assert "max_value" in result.violations[0].reason

    def test_non_numeric_with_numeric_rule(self, checker):
        checker.add_rule("PORT", BoundaryRule(min_value=0))
        result = checker.check({"PORT": "not-a-number"})
        assert not result.is_clean
        assert "not numeric" in result.violations[0].reason

    def test_key_not_in_rules_is_skipped(self, checker):
        checker.add_rule("OTHER", BoundaryRule(min_length=100))
        result = checker.check({"NAME": "hi"})
        assert result.is_clean

    def test_multiple_violations(self, checker):
        checker.add_rule("A", BoundaryRule(min_length=10))
        checker.add_rule("B", BoundaryRule(max_value=5.0))
        result = checker.check({"A": "short", "B": "99"})
        assert len(result.violations) == 2
