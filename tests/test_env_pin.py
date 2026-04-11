"""Tests for envoy.env_pin."""
import pytest
from envoy.env_pin import EnvPinner, PinResult, PinViolation


@pytest.fixture
def pinner():
    return EnvPinner(pins={
        "NODE_ENV": "production",
        "LOG_LEVEL": "re:[a-z]+",
    })


@pytest.fixture
def sample_vars():
    return {"NODE_ENV": "production", "LOG_LEVEL": "info", "PORT": "8080"}


class TestPinResult:
    def test_repr(self):
        r = PinResult(pinned_count=3, violations=[])
        assert "pinned=3" in repr(r)
        assert "clean=True" in repr(r)

    def test_is_clean_when_no_violations(self):
        r = PinResult(pinned_count=1, violations=[])
        assert r.is_clean is True

    def test_not_clean_with_violation(self):
        v = PinViolation(key="X", expected="y", actual="z", reason="mismatch")
        r = PinResult(pinned_count=1, violations=[v])
        assert r.is_clean is False


class TestPinViolation:
    def test_repr_contains_key_and_reason(self):
        v = PinViolation(key="FOO", expected="bar", actual="baz", reason="value mismatch")
        assert "FOO" in repr(v)
        assert "value mismatch" in repr(v)


class TestEnvPinner:
    def test_clean_when_all_pins_satisfied(self, pinner, sample_vars):
        result = pinner.check(sample_vars)
        assert result.is_clean
        assert result.pinned_count == 2

    def test_violation_on_literal_mismatch(self, pinner):
        vars = {"NODE_ENV": "development", "LOG_LEVEL": "debug"}
        result = pinner.check(vars)
        assert not result.is_clean
        keys = [v.key for v in result.violations]
        assert "NODE_ENV" in keys

    def test_violation_on_missing_key(self, pinner):
        result = pinner.check({"PORT": "3000"})
        assert not result.is_clean
        reasons = {v.key: v.reason for v in result.violations}
        assert reasons["NODE_ENV"] == "key missing"
        assert reasons["LOG_LEVEL"] == "key missing"

    def test_violation_on_pattern_mismatch(self, pinner):
        vars = {"NODE_ENV": "production", "LOG_LEVEL": "INFO"}
        result = pinner.check(vars)
        assert not result.is_clean
        assert result.violations[0].key == "LOG_LEVEL"
        assert "pattern" in result.violations[0].reason

    def test_pattern_pin_passes_on_valid_value(self, pinner):
        vars = {"NODE_ENV": "production", "LOG_LEVEL": "warn"}
        result = pinner.check(vars)
        assert result.is_clean

    def test_apply_forces_literal_pins(self, pinner):
        vars = {"NODE_ENV": "development", "LOG_LEVEL": "debug", "PORT": "3000"}
        applied = pinner.apply(vars)
        assert applied["NODE_ENV"] == "production"
        assert applied["LOG_LEVEL"] == "debug"  # pattern pin skipped
        assert applied["PORT"] == "3000"

    def test_apply_adds_missing_literal_pin(self, pinner):
        applied = pinner.apply({"LOG_LEVEL": "info"})
        assert applied["NODE_ENV"] == "production"

    def test_empty_pins_always_clean(self):
        p = EnvPinner(pins={})
        result = p.check({"FOO": "bar"})
        assert result.is_clean
        assert result.pinned_count == 0
