"""Tests for EnvFilter."""
import pytest
from envoy.env_filter import EnvFilter, FilterResult


SAMPLE_VARS = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "AWS_ACCESS_KEY_ID": "AKIA123",
    "AWS_SECRET": "secret",
    "APP_DEBUG": "true",
    "LOG_LEVEL": "info",
    "FEATURE_FLAG_X": "1",
}


@pytest.fixture
def f() -> EnvFilter:
    return EnvFilter()


class TestFilterResult:
    def test_repr(self):
        r = FilterResult(matched={"A": "1"}, excluded={"B": "2"}, total=2)
        assert "matched=1" in repr(r)
        assert "excluded=1" in repr(r)
        assert "total=2" in repr(r)


class TestEnvFilter:
    def test_no_rules_matches_all(self, f):
        result = f.apply(SAMPLE_VARS)
        assert result.matched == SAMPLE_VARS
        assert result.excluded == {}
        assert result.total == len(SAMPLE_VARS)

    def test_prefix_filter(self):
        flt = EnvFilter(prefixes=["DB_"])
        result = flt.apply(SAMPLE_VARS)
        assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT"}
        assert "APP_DEBUG" in result.excluded

    def test_multiple_prefixes(self):
        flt = EnvFilter(prefixes=["DB_", "AWS_"])
        result = flt.apply(SAMPLE_VARS)
        assert "DB_HOST" in result.matched
        assert "AWS_ACCESS_KEY_ID" in result.matched
        assert "LOG_LEVEL" in result.excluded

    def test_glob_pattern_filter(self):
        flt = EnvFilter(patterns=["FEATURE_*"])
        result = flt.apply(SAMPLE_VARS)
        assert "FEATURE_FLAG_X" in result.matched
        assert "DB_HOST" in result.excluded

    def test_regex_filter(self):
        flt = EnvFilter(regex=r"^DB_")
        result = flt.apply(SAMPLE_VARS)
        assert "DB_HOST" in result.matched
        assert "DB_PORT" in result.matched
        assert "APP_DEBUG" in result.excluded

    def test_exclude_prefix(self):
        flt = EnvFilter(exclude_prefixes=["AWS_"])
        result = flt.apply(SAMPLE_VARS)
        assert "AWS_ACCESS_KEY_ID" in result.excluded
        assert "AWS_SECRET" in result.excluded
        assert "DB_HOST" in result.matched

    def test_exclude_pattern(self):
        flt = EnvFilter(exclude_patterns=["*_KEY*", "*SECRET*"])
        result = flt.apply(SAMPLE_VARS)
        assert "AWS_ACCESS_KEY_ID" in result.excluded
        assert "AWS_SECRET" in result.excluded
        assert "DB_HOST" in result.matched

    def test_include_and_exclude_combined(self):
        flt = EnvFilter(prefixes=["AWS_"], exclude_patterns=["*SECRET*"])
        result = flt.apply(SAMPLE_VARS)
        assert "AWS_ACCESS_KEY_ID" in result.matched
        assert "AWS_SECRET" in result.excluded
        assert "DB_HOST" in result.excluded

    def test_total_count_preserved(self):
        flt = EnvFilter(prefixes=["DB_"])
        result = flt.apply(SAMPLE_VARS)
        assert result.total == len(SAMPLE_VARS)
        assert len(result.matched) + len(result.excluded) == result.total

    def test_empty_vars(self, f):
        result = f.apply({})
        assert result.matched == {}
        assert result.excluded == {}
        assert result.total == 0
