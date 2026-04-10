"""Tests for EnvLinter."""
import pytest
from envoy.env_lint import EnvLinter, LintResult, LintIssue


@pytest.fixture
def linter() -> EnvLinter:
    return EnvLinter()


class TestLintResult:
    def test_passed_with_no_errors(self):
        result = LintResult(issues=[LintIssue(key="K", message="note", severity="info")])
        assert result.passed is True

    def test_failed_with_error(self):
        result = LintResult(issues=[LintIssue(key="K", message="bad", severity="error")])
        assert result.passed is False

    def test_warnings_filtered(self):
        result = LintResult(issues=[
            LintIssue(key="A", message="w", severity="warning"),
            LintIssue(key="B", message="e", severity="error"),
        ])
        assert len(result.warnings) == 1
        assert len(result.errors) == 1


class TestEnvLinter:
    def test_valid_vars_pass(self, linter):
        result = linter.lint({"DATABASE_URL": "postgres://localhost/db", "PORT": "5432"})
        assert result.passed
        assert result.errors == []

    def test_lowercase_key_produces_warning(self, linter):
        result = linter.lint({"database_url": "value"})
        keys = [i.key for i in result.warnings]
        assert "database_url" in keys

    def test_key_starting_with_digit_is_error(self, linter):
        result = linter.lint({"1BAD_KEY": "value"})
        assert not result.passed
        assert any("start with" in i.message for i in result.errors)

    def test_key_with_hyphen_is_error(self, linter):
        result = linter.lint({"BAD-KEY": "value"})
        assert not result.passed
        assert any("invalid characters" in i.message for i in result.errors)

    def test_empty_value_produces_info(self, linter):
        result = linter.lint({"MY_VAR": ""})
        info_issues = [i for i in result.issues if i.severity == "info"]
        assert any(i.key == "MY_VAR" for i in info_issues)

    def test_value_with_leading_whitespace_warns(self, linter):
        result = linter.lint({"MY_VAR": "  spaced"})
        assert any("whitespace" in i.message for i in result.warnings)

    def test_value_exceeding_max_length_warns(self, linter):
        long_value = "x" * 600
        result = linter.lint({"BIG_VAR": long_value})
        assert any("exceeds" in i.message and i.key == "BIG_VAR" for i in result.warnings)

    def test_key_exceeding_max_length_warns(self, linter):
        long_key = "A" * 70
        result = linter.lint({long_key: "value"})
        assert any("exceeds" in i.message and i.key == long_key for i in result.warnings)

    def test_empty_vars_dict_passes(self, linter):
        result = linter.lint({})
        assert result.passed
        assert result.issues == []

    def test_repr_contains_counts(self, linter):
        result = linter.lint({"bad-key": "value"})
        r = repr(result)
        assert "errors=" in r
        assert "warnings=" in r
