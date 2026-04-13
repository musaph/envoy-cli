import pytest
from envoy.env_sanitize import EnvSanitizer, SanitizeChange, SanitizeResult


@pytest.fixture
def sanitizer():
    return EnvSanitizer()


@pytest.fixture
def strict_sanitizer():
    return EnvSanitizer(strip_whitespace=True, remove_control_chars=True, max_length=20)


class TestSanitizeResult:
    def test_repr(self):
        r = SanitizeResult()
        assert "SanitizeResult" in repr(r)
        assert "has_changes=False" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = SanitizeResult()
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        change = SanitizeChange(key="K", original="v ", sanitized="v", reason="stripped")
        r = SanitizeResult(changes=[change], sanitized={"K": "v"})
        assert r.has_changes


class TestSanitizeChange:
    def test_repr_contains_key_and_reason(self):
        c = SanitizeChange(key="FOO", original="bar ", sanitized="bar", reason="stripped")
        assert "FOO" in repr(c)
        assert "stripped" in repr(c)


class TestEnvSanitizer:
    def test_clean_vars_produce_no_changes(self, sanitizer):
        vars_ = {"KEY": "value", "PORT": "8080"}
        result = sanitizer.sanitize(vars_)
        assert not result.has_changes
        assert result.sanitized == vars_

    def test_strips_leading_trailing_whitespace(self, sanitizer):
        vars_ = {"KEY": "  hello  "}
        result = sanitizer.sanitize(vars_)
        assert result.has_changes
        assert result.sanitized["KEY"] == "hello"
        assert result.changes[0].reason == "stripped surrounding whitespace"

    def test_removes_control_characters(self, sanitizer):
        vars_ = {"KEY": "val\x01ue"}
        result = sanitizer.sanitize(vars_)
        assert result.has_changes
        assert result.sanitized["KEY"] == "value"
        assert "control" in result.changes[0].reason

    def test_max_length_truncates_value(self, strict_sanitizer):
        vars_ = {"KEY": "a" * 30}
        result = strict_sanitizer.sanitize(vars_)
        assert result.has_changes
        assert len(result.sanitized["KEY"]) == 20
        assert "truncated" in result.changes[0].reason

    def test_no_strip_preserves_whitespace(self):
        s = EnvSanitizer(strip_whitespace=False)
        vars_ = {"KEY": "  spaced  "}
        result = s.sanitize(vars_)
        assert not result.has_changes
        assert result.sanitized["KEY"] == "  spaced  "

    def test_multiple_issues_combined_in_reason(self, strict_sanitizer):
        vars_ = {"KEY": "  " + "x" * 25 + "  "}
        result = strict_sanitizer.sanitize(vars_)
        assert result.has_changes
        reason = result.changes[0].reason
        assert "whitespace" in reason
        assert "truncated" in reason

    def test_multiple_vars_tracked_independently(self, sanitizer):
        vars_ = {"A": "  hello", "B": "clean", "C": "world  "}
        result = sanitizer.sanitize(vars_)
        changed_keys = {c.key for c in result.changes}
        assert "A" in changed_keys
        assert "B" not in changed_keys
        assert "C" in changed_keys
