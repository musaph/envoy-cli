"""Tests for envoy.env_defaults."""
import pytest
from envoy.env_defaults import DefaultEntry, DefaultsResult, EnvDefaultsManager


@pytest.fixture
def manager():
    return EnvDefaultsManager(
        defaults={"HOST": "localhost", "PORT": "8080", "DEBUG": "false"}
    )


@pytest.fixture
def sample_vars():
    return {"HOST": "prod.example.com", "PORT": ""}


class TestDefaultEntry:
    def test_to_dict_roundtrip(self):
        entry = DefaultEntry(key="FOO", default_value="bar", description="A foo var")
        assert DefaultEntry.from_dict(entry.to_dict()) == entry

    def test_repr_contains_key_and_default(self):
        entry = DefaultEntry(key="X", default_value="y")
        r = repr(entry)
        assert "X" in r
        assert "y" in r

    def test_from_dict_missing_description_defaults_empty(self):
        entry = DefaultEntry.from_dict({"key": "K", "default_value": "v"})
        assert entry.description == ""


class TestDefaultsResult:
    def test_repr(self):
        r = DefaultsResult(applied={"A": "1"}, skipped={"B": "2", "C": "3"})
        assert "1" in repr(r)
        assert "2" in repr(r)

    def test_has_applied_false_when_empty(self):
        r = DefaultsResult()
        assert not r.has_applied

    def test_has_applied_true_when_populated(self):
        r = DefaultsResult(applied={"X": "v"})
        assert r.has_applied


class TestEnvDefaultsManager:
    def test_missing_key_gets_default(self, manager):
        result = manager.apply({"HOST": "localhost"})
        assert "PORT" in result.applied
        assert "DEBUG" in result.applied

    def test_existing_non_empty_key_is_skipped(self, manager, sample_vars):
        result = manager.apply(sample_vars)
        assert "HOST" in result.skipped
        assert result.skipped["HOST"] == "prod.example.com"

    def test_empty_value_overwritten_by_default(self, manager, sample_vars):
        result = manager.apply(sample_vars)
        assert "PORT" in result.applied
        assert result.applied["PORT"] == "8080"

    def test_empty_value_not_overwritten_when_flag_false(self):
        mgr = EnvDefaultsManager(
            defaults={"PORT": "8080"}, overwrite_empty=False
        )
        result = mgr.apply({"PORT": ""})
        assert "PORT" in result.skipped
        assert "PORT" not in result.applied

    def test_apply_does_not_mutate_input(self, manager):
        original = {"HOST": "h"}
        manager.apply(original)
        assert original == {"HOST": "h"}

    def test_missing_keys_returns_absent_keys(self, manager):
        missing = manager.missing_keys({"HOST": "h"})
        assert "PORT" in missing
        assert "DEBUG" in missing
        assert "HOST" not in missing

    def test_missing_keys_with_required_subset(self, manager):
        missing = manager.missing_keys({"HOST": "h"}, required=["HOST", "PORT"])
        assert missing == ["PORT"]

    def test_all_present_returns_no_missing(self, manager):
        vars = {"HOST": "h", "PORT": "9", "DEBUG": "true"}
        assert manager.missing_keys(vars) == []
