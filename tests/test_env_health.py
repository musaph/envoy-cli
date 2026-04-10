"""Tests for EnvHealthChecker and HealthReport."""
import pytest
from envoy.env_health import EnvHealthChecker, HealthIssue, HealthReport


@pytest.fixture
def checker() -> EnvHealthChecker:
    return EnvHealthChecker()


@pytest.fixture
def checker_with_required() -> EnvHealthChecker:
    return EnvHealthChecker(required_keys=["DATABASE_URL", "SECRET_KEY"])


class TestHealthReport:
    def test_is_healthy_with_no_issues(self):
        report = HealthReport()
        assert report.is_healthy is True

    def test_is_unhealthy_with_error(self):
        report = HealthReport(issues=[HealthIssue("error", "FOO", "bad")])
        assert report.is_healthy is False

    def test_warnings_do_not_affect_health(self):
        report = HealthReport(issues=[HealthIssue("warning", "BAR", "empty")])
        assert report.is_healthy is True

    def test_errors_property_filters_correctly(self):
        report = HealthReport(
            issues=[
                HealthIssue("error", "A", "missing"),
                HealthIssue("warning", "B", "empty"),
            ]
        )
        assert len(report.errors) == 1
        assert len(report.warnings) == 1

    def test_summary_contains_counts(self):
        report = HealthReport(
            issues=[HealthIssue("error", "X", "msg")]
        )
        summary = report.summary()
        assert "1 error" in summary
        assert "unhealthy" in summary


class TestEnvHealthChecker:
    def test_healthy_vars_produce_no_issues(self, checker):
        report = checker.check({"APP_ENV": "production", "PORT": "8080"})
        assert report.is_healthy
        assert report.issues == []

    def test_empty_value_produces_warning(self, checker):
        report = checker.check({"API_KEY": ""})
        assert report.is_healthy  # warning only
        assert any(i.key == "API_KEY" and i.level == "warning" for i in report.issues)

    def test_whitespace_only_value_produces_warning(self, checker):
        report = checker.check({"TOKEN": "   "})
        assert any(i.level == "warning" and i.key == "TOKEN" for i in report.issues)

    def test_missing_required_key_is_error(self, checker_with_required):
        report = checker_with_required.check({"APP_ENV": "dev"})
        missing_keys = {i.key for i in report.errors}
        assert "DATABASE_URL" in missing_keys
        assert "SECRET_KEY" in missing_keys

    def test_present_required_keys_no_error(self, checker_with_required):
        report = checker_with_required.check(
            {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc123"}
        )
        assert report.is_healthy

    def test_empty_vars_with_required_keys_reports_all_missing(self, checker_with_required):
        report = checker_with_required.check({})
        assert len(report.errors) == 2

    def test_repr_of_issue_with_key(self):
        issue = HealthIssue("error", "MY_KEY", "some problem")
        assert "MY_KEY" in repr(issue)
        assert "error" in repr(issue)

    def test_repr_of_issue_without_key(self):
        issue = HealthIssue("info", None, "general note")
        assert "general note" in repr(issue)
