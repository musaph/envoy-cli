"""Tests for envoy.env_compare module."""
import pytest
from envoy.env_compare import CompareEntry, CompareReport, EnvComparer


@pytest.fixture
def comparer() -> EnvComparer:
    return EnvComparer()


@pytest.fixture
def sample_local() -> dict:
    return {"APP_ENV": "production", "DB_HOST": "localhost", "ONLY_LOCAL": "yes"}


@pytest.fixture
def sample_remote() -> dict:
    return {"APP_ENV": "staging", "DB_HOST": "localhost", "ONLY_REMOTE": "true"}


class TestCompareEntry:
    def test_repr_contains_key_and_status(self):
        entry = CompareEntry("MY_KEY", "a", "b", "differ")
        r = repr(entry)
        assert "MY_KEY" in r
        assert "differ" in r


class TestCompareReport:
    def test_repr_shows_counts(self):
        report = CompareReport()
        r = repr(report)
        assert "matches=" in r
        assert "differ=" in r

    def test_is_identical_empty(self):
        assert CompareReport().is_identical is True

    def test_is_identical_all_match(self):
        entries = [CompareEntry("K", "v", "v", "match")]
        assert CompareReport(entries=entries).is_identical is True

    def test_is_not_identical_with_differ(self):
        entries = [CompareEntry("K", "a", "b", "differ")]
        assert CompareReport(entries=entries).is_identical is False

    def test_is_not_identical_with_local_only(self):
        entries = [CompareEntry("K", "a", None, "local_only")]
        assert CompareReport(entries=entries).is_identical is False


class TestEnvComparer:
    def test_identical_dicts_produce_all_matches(self, comparer):
        vars_ = {"A": "1", "B": "2"}
        report = comparer.compare(vars_, vars_.copy())
        assert report.is_identical
        assert len(report.matches) == 2
        assert len(report.differences) == 0

    def test_differing_value_detected(self, comparer, sample_local, sample_remote):
        report = comparer.compare(sample_local, sample_remote)
        differ_keys = [e.key for e in report.differences]
        assert "APP_ENV" in differ_keys

    def test_matching_value_detected(self, comparer, sample_local, sample_remote):
        report = comparer.compare(sample_local, sample_remote)
        match_keys = [e.key for e in report.matches]
        assert "DB_HOST" in match_keys

    def test_local_only_key_detected(self, comparer, sample_local, sample_remote):
        report = comparer.compare(sample_local, sample_remote)
        local_keys = [e.key for e in report.local_only]
        assert "ONLY_LOCAL" in local_keys

    def test_remote_only_key_detected(self, comparer, sample_local, sample_remote):
        report = comparer.compare(sample_local, sample_remote)
        remote_keys = [e.key for e in report.remote_only]
        assert "ONLY_REMOTE" in remote_keys

    def test_empty_dicts_produce_empty_report(self, comparer):
        report = comparer.compare({}, {})
        assert report.is_identical
        assert report.entries == []

    def test_keys_are_sorted_in_output(self, comparer):
        local = {"Z_KEY": "1", "A_KEY": "1"}
        remote = {"Z_KEY": "1", "A_KEY": "1"}
        report = comparer.compare(local, remote)
        keys = [e.key for e in report.entries]
        assert keys == sorted(keys)

    def test_entry_values_preserved(self, comparer):
        report = comparer.compare({"X": "local_val"}, {"X": "remote_val"})
        entry = report.entries[0]
        assert entry.local_value == "local_val"
        assert entry.remote_value == "remote_val"
        assert entry.status == "differ"
