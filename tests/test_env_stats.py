"""Tests for EnvStatsCalculator."""
import pytest
from envoy.env_stats import EnvStats, EnvStatsCalculator


@pytest.fixture
def calc() -> EnvStatsCalculator:
    return EnvStatsCalculator()


@pytest.fixture
def sample_vars():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "APP_DEBUG": "true",
        "APP_NAME": "myapp",
        "EMPTY_VAR": "",
        "DUPLICATE_A": "same",
        "DUPLICATE_B": "same",
    }


class TestEnvStats:
    def test_repr(self):
        s = EnvStats(total=5, empty_values=1, sensitive_keys=2, duplicate_values=0)
        assert "total=5" in repr(s)
        assert "empty=1" in repr(s)


class TestEnvStatsCalculator:
    def test_empty_vars_returns_zero_stats(self, calc):
        stats = calc.compute({})
        assert stats.total == 0
        assert stats.empty_values == 0
        assert stats.sensitive_keys == 0

    def test_total_count(self, calc, sample_vars):
        stats = calc.compute(sample_vars)
        assert stats.total == len(sample_vars)

    def test_empty_values_counted(self, calc, sample_vars):
        stats = calc.compute(sample_vars)
        assert stats.empty_values == 1

    def test_sensitive_keys_detected(self, calc, sample_vars):
        stats = calc.compute(sample_vars)
        # DB_PASSWORD and API_KEY should be flagged
        assert stats.sensitive_keys >= 2

    def test_duplicate_values_counted(self, calc, sample_vars):
        stats = calc.compute(sample_vars)
        # DUPLICATE_A and DUPLICATE_B share "same"
        assert stats.duplicate_values == 2

    def test_no_duplicates_when_all_unique(self, calc):
        vars = {"A": "1", "B": "2", "C": "3"}
        stats = calc.compute(vars)
        assert stats.duplicate_values == 0

    def test_longest_key(self, calc):
        vars = {"SHORT": "x", "A_VERY_LONG_KEY_NAME": "y", "MID_KEY": "z"}
        stats = calc.compute(vars)
        assert stats.longest_key == "A_VERY_LONG_KEY_NAME"

    def test_longest_value_key(self, calc):
        vars = {"A": "hi", "B": "a much longer value here", "C": "ok"}
        stats = calc.compute(vars)
        assert stats.longest_value_key == "B"

    def test_prefix_grouping(self, calc, sample_vars):
        stats = calc.compute(sample_vars)
        assert stats.prefixes.get("DB") == 3
        assert stats.prefixes.get("APP") == 2
        assert stats.prefixes.get("API") == 1

    def test_no_prefix_keys_excluded(self, calc):
        vars = {"NOPREFIX": "val"}
        stats = calc.compute(vars)
        assert stats.prefixes == {}

    def test_summary_lines_contain_totals(self, calc, sample_vars):
        stats = calc.compute(sample_vars)
        lines = calc.summary_lines(stats)
        joined = "\n".join(lines)
        assert str(stats.total) in joined
        assert str(stats.empty_values) in joined
        assert str(stats.sensitive_keys) in joined

    def test_summary_lines_include_prefixes(self, calc, sample_vars):
        stats = calc.compute(sample_vars)
        lines = calc.summary_lines(stats)
        assert any("DB" in line for line in lines)
