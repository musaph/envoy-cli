"""Tests for envoy.env_interpolate."""
import pytest
from envoy.env_interpolate import EnvInterpolator, InterpolationResult


@pytest.fixture
def interp() -> EnvInterpolator:
    return EnvInterpolator()


class TestInterpolationResult:
    def test_is_clean_when_no_issues(self):
        r = InterpolationResult(resolved={"A": "1"})
        assert r.is_clean is True

    def test_not_clean_with_unresolved(self):
        r = InterpolationResult(resolved={}, unresolved_keys=["X"])
        assert r.is_clean is False

    def test_not_clean_with_cycles(self):
        r = InterpolationResult(resolved={}, cycles=["Y"])
        assert r.is_clean is False


class TestEnvInterpolator:
    def test_no_references_unchanged(self, interp):
        result = interp.interpolate({"FOO": "bar", "NUM": "42"})
        assert result.resolved == {"FOO": "bar", "NUM": "42"}
        assert result.is_clean

    def test_curly_brace_syntax(self, interp):
        result = interp.interpolate({"BASE": "/app", "LOG": "${BASE}/logs"})
        assert result.resolved["LOG"] == "/app/logs"
        assert result.is_clean

    def test_bare_dollar_syntax(self, interp):
        result = interp.interpolate({"HOST": "localhost", "URL": "http://$HOST:8080"})
        assert result.resolved["URL"] == "http://localhost:8080"
        assert result.is_clean

    def test_chained_references(self, interp):
        vars = {"A": "hello", "B": "${A}_world", "C": "${B}!"}
        result = interp.interpolate(vars)
        assert result.resolved["C"] == "hello_world!"
        assert result.is_clean

    def test_context_provides_external_values(self, interp):
        result = interp.interpolate(
            {"FULL": "${PREFIX}_suffix"},
            context={"PREFIX": "my"},
        )
        assert result.resolved["FULL"] == "my_suffix"
        assert result.is_clean

    def test_vars_override_context(self, interp):
        result = interp.interpolate(
            {"X": "from_vars", "Y": "${X}"},
            context={"X": "from_context"},
        )
        assert result.resolved["Y"] == "from_vars"

    def test_unresolved_reference_recorded(self, interp):
        result = interp.interpolate({"FOO": "${MISSING}_value"})
        assert "FOO" in result.unresolved_keys
        assert result.resolved["FOO"] == "${MISSING}_value"  # original kept
        assert not result.is_clean

    def test_cycle_detected(self, interp):
        result = interp.interpolate({"A": "${B}", "B": "${A}"})
        # at least one of A/B should be flagged as a cycle
        assert result.cycles
        assert not result.is_clean

    def test_multiple_refs_in_one_value(self, interp):
        result = interp.interpolate(
            {"H": "localhost", "P": "5432", "DSN": "postgres://${H}:${P}/db"}
        )
        assert result.resolved["DSN"] == "postgres://localhost:5432/db"
        assert result.is_clean

    def test_empty_vars_returns_empty(self, interp):
        result = interp.interpolate({})
        assert result.resolved == {}
        assert result.is_clean

    def test_context_only_value_not_in_resolved(self, interp):
        """Keys present only in context should not appear in resolved output."""
        result = interp.interpolate(
            {"GREETING": "Hello, ${NAME}!"},
            context={"NAME": "World"},
        )
        assert result.resolved["GREETING"] == "Hello, World!"
        assert "NAME" not in result.resolved
        assert result.is_clean
