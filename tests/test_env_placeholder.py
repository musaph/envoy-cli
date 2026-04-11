"""Tests for EnvPlaceholderDetector."""
import pytest
from envoy.env_placeholder import (
    EnvPlaceholderDetector,
    PlaceholderMatch,
    PlaceholderResult,
)


@pytest.fixture
def detector():
    return EnvPlaceholderDetector()


class TestPlaceholderResult:
    def test_repr(self):
        r = PlaceholderResult(matches=[], checked=5)
        assert "False" in repr(r)
        assert "0/5" in repr(r)

    def test_found_false_when_empty(self):
        r = PlaceholderResult()
        assert r.found is False

    def test_found_true_when_matches(self):
        m = PlaceholderMatch(key="K", value="<VAL>", reason="pattern")
        r = PlaceholderResult(matches=[m], checked=1)
        assert r.found is True


class TestEnvPlaceholderDetector:
    def test_empty_value_is_placeholder(self, detector):
        reason = detector.is_placeholder("")
        assert reason is not None
        assert "empty" in reason

    def test_angle_bracket_placeholder(self, detector):
        assert detector.is_placeholder("<YOUR_SECRET>") is not None

    def test_double_brace_placeholder(self, detector):
        assert detector.is_placeholder("{{my_placeholder}}") is not None

    def test_change_me_placeholder(self, detector):
        assert detector.is_placeholder("CHANGE_ME") is not None

    def test_todo_placeholder(self, detector):
        assert detector.is_placeholder("TODO") is not None

    def test_replace_me_placeholder(self, detector):
        assert detector.is_placeholder("REPLACE_ME") is not None

    def test_your_prefix_placeholder(self, detector):
        assert detector.is_placeholder("YOUR_API_KEY") is not None

    def test_real_value_not_placeholder(self, detector):
        assert detector.is_placeholder("supersecret123") is None

    def test_detect_returns_result(self, detector):
        vars = {"KEY": "value", "SECRET": "<YOUR_SECRET>", "EMPTY": ""}
        result = detector.detect(vars)
        assert result.checked == 3
        assert result.found is True
        keys = [m.key for m in result.matches]
        assert "SECRET" in keys
        assert "EMPTY" in keys
        assert "KEY" not in keys

    def test_detect_no_placeholders(self, detector):
        vars = {"HOST": "localhost", "PORT": "5432"}
        result = detector.detect(vars)
        assert result.found is False
        assert result.checked == 2

    def test_extra_patterns(self):
        import re
        det = EnvPlaceholderDetector(extra_patterns=[re.compile(r'^CUSTOM_PLACEHOLDER$')])
        assert det.is_placeholder("CUSTOM_PLACEHOLDER") is not None
        assert det.is_placeholder("real_value") is None

    def test_placeholder_match_repr(self):
        m = PlaceholderMatch(key="X", value="<Y>", reason="angle brackets")
        assert "X" in repr(m)
        assert "angle brackets" in repr(m)
