"""Tests for EnvExtractor."""
import pytest
from envoy.env_extract import EnvExtractor, ExtractResult


@pytest.fixture
def extractor() -> EnvExtractor:
    return EnvExtractor()


@pytest.fixture
def sample_vars() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_NAME": "envoy",
        "APP_DEBUG": "true",
        "SECRET_KEY": "abc123",
    }


class TestExtractResult:
    def test_repr(self):
        r = ExtractResult(extracted={"A": "1"}, missing_keys=["B"])
        assert "ExtractResult" in repr(r)

    def test_has_missing_false_when_empty(self):
        r = ExtractResult()
        assert r.has_missing is False

    def test_has_missing_true_when_populated(self):
        r = ExtractResult(missing_keys=["MISSING"])
        assert r.has_missing is True


class TestEnvExtractorByKeys:
    def test_extract_existing_keys(self, extractor, sample_vars):
        result = extractor.extract_keys(sample_vars, ["DB_HOST", "APP_NAME"])
        assert result.extracted == {"DB_HOST": "localhost", "APP_NAME": "envoy"}
        assert result.missing_keys == []

    def test_missing_key_reported(self, extractor, sample_vars):
        result = extractor.extract_keys(sample_vars, ["DB_HOST", "NONEXISTENT"])
        assert "NONEXISTENT" in result.missing_keys
        assert "DB_HOST" in result.extracted

    def test_ignore_missing_suppresses_missing(self, sample_vars):
        ex = EnvExtractor(ignore_missing=True)
        result = ex.extract_keys(sample_vars, ["DB_HOST", "NONEXISTENT"])
        assert result.missing_keys == []
        assert "DB_HOST" in result.extracted

    def test_empty_keys_returns_empty(self, extractor, sample_vars):
        result = extractor.extract_keys(sample_vars, [])
        assert result.extracted == {}
        assert result.missing_keys == []


class TestEnvExtractorByPattern:
    def test_pattern_matches_prefix(self, extractor, sample_vars):
        result = extractor.extract_pattern(sample_vars, r"^DB_")
        assert set(result.extracted.keys()) == {"DB_HOST", "DB_PORT"}
        assert result.matched_pattern == r"^DB_"

    def test_pattern_matches_suffix(self, extractor, sample_vars):
        result = extractor.extract_pattern(sample_vars, r"_KEY$")
        assert "SECRET_KEY" in result.extracted

    def test_pattern_no_match_returns_empty(self, extractor, sample_vars):
        result = extractor.extract_pattern(sample_vars, r"^ZZZZZ")
        assert result.extracted == {}

    def test_invalid_pattern_raises(self, extractor, sample_vars):
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            extractor.extract_pattern(sample_vars, r"[invalid")


class TestEnvExtractorByPrefix:
    def test_extract_by_prefix(self, extractor, sample_vars):
        result = extractor.extract_prefix(sample_vars, "APP_")
        assert set(result.extracted.keys()) == {"APP_NAME", "APP_DEBUG"}

    def test_strip_prefix(self, extractor, sample_vars):
        result = extractor.extract_prefix(sample_vars, "APP_", strip_prefix=True)
        assert "NAME" in result.extracted
        assert "DEBUG" in result.extracted
        assert result.extracted["NAME"] == "envoy"

    def test_no_match_returns_empty(self, extractor, sample_vars):
        result = extractor.extract_prefix(sample_vars, "NOPE_")
        assert result.extracted == {}
