"""Tests for envoy.env_dotdiff."""
import pytest
from envoy.env_dotdiff import DotDiffEntry, DotDiffResult, EnvDotDiffer


@pytest.fixture
def differ() -> EnvDotDiffer:
    return EnvDotDiffer()


@pytest.fixture
def sample_old() -> dict:
    return {"APP_ENV": "development", "DB_HOST": "localhost", "LOG_LEVEL": "debug"}


@pytest.fixture
def sample_new() -> dict:
    return {"APP_ENV": "production", "DB_HOST": "localhost", "NEW_KEY": "value"}


# --- DotDiffEntry ---

class TestDotDiffEntry:
    def test_repr_contains_key_and_status(self):
        e = DotDiffEntry("FOO", "bar", None, "removed")
        assert "FOO" in repr(e)
        assert "removed" in repr(e)


# --- DotDiffResult ---

class TestDotDiffResult:
    def test_repr(self):
        r = DotDiffResult()
        assert "DotDiffResult" in repr(r)

    def test_has_diff_false_when_empty(self):
        assert not DotDiffResult().has_diff

    def test_has_diff_true_when_entries(self):
        r = DotDiffResult(entries=[DotDiffEntry("X", None, "1", "added")])
        assert r.has_diff

    def test_category_properties(self):
        entries = [
            DotDiffEntry("A", None, "1", "added"),
            DotDiffEntry("B", "2", None, "removed"),
            DotDiffEntry("C", "3", "4", "changed"),
            DotDiffEntry("D", "5", "5", "unchanged"),
        ]
        r = DotDiffResult(entries=entries)
        assert len(r.added) == 1
        assert len(r.removed) == 1
        assert len(r.changed) == 1
        assert len(r.unchanged) == 1


# --- EnvDotDiffer ---

class TestEnvDotDiffer:
    def test_identical_dicts_no_diff(self, differ, sample_old):
        result = differ.diff(sample_old, sample_old)
        assert not result.has_diff

    def test_detects_added_key(self, differ, sample_old, sample_new):
        result = differ.diff(sample_old, sample_new)
        keys = [e.key for e in result.added]
        assert "NEW_KEY" in keys

    def test_detects_removed_key(self, differ, sample_old, sample_new):
        result = differ.diff(sample_old, sample_new)
        keys = [e.key for e in result.removed]
        assert "LOG_LEVEL" in keys

    def test_detects_changed_value(self, differ, sample_old, sample_new):
        result = differ.diff(sample_old, sample_new)
        keys = [e.key for e in result.changed]
        assert "APP_ENV" in keys

    def test_unchanged_not_included_by_default(self, differ, sample_old, sample_new):
        result = differ.diff(sample_old, sample_new)
        assert len(result.unchanged) == 0

    def test_include_unchanged_flag(self, differ, sample_old, sample_new):
        result = differ.diff(sample_old, sample_new, include_unchanged=True)
        keys = [e.key for e in result.unchanged]
        assert "DB_HOST" in keys

    def test_ignore_case_treats_same_value_as_unchanged(self):
        d = EnvDotDiffer(ignore_case=True)
        result = d.diff({"KEY": "Value"}, {"KEY": "value"})
        assert not result.has_diff

    def test_case_sensitive_detects_change(self, differ):
        result = differ.diff({"KEY": "Value"}, {"KEY": "value"})
        assert result.has_diff
        assert result.changed[0].key == "KEY"

    def test_empty_old_all_added(self, differ, sample_new):
        result = differ.diff({}, sample_new)
        assert len(result.added) == len(sample_new)
        assert not result.removed

    def test_empty_new_all_removed(self, differ, sample_old):
        result = differ.diff(sample_old, {})
        assert len(result.removed) == len(sample_old)
        assert not result.added
