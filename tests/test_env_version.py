import pytest
from envoy.env_version import VersionEntry, VersionResult, EnvVersionManager


@pytest.fixture
def manager():
    return EnvVersionManager(max_versions=5)


@pytest.fixture
def sample_vars():
    return {"APP_ENV": "production", "DB_HOST": "localhost", "PORT": "8080"}


class TestVersionEntry:
    def test_to_dict_roundtrip(self):
        e = VersionEntry(version=1, vars={"A": "1"}, label="initial")
        d = e.to_dict()
        restored = VersionEntry.from_dict(d)
        assert restored.version == 1
        assert restored.vars == {"A": "1"}
        assert restored.label == "initial"

    def test_repr_with_label(self):
        e = VersionEntry(version=2, vars={"X": "y", "Z": "w"}, label="release")
        r = repr(e)
        assert "v2" in r
        assert "release" in r
        assert "keys=2" in r

    def test_repr_without_label(self):
        e = VersionEntry(version=3, vars={})
        r = repr(e)
        assert "v3" in r
        assert "keys=0" in r

    def test_from_dict_missing_label_defaults_none(self):
        e = VersionEntry.from_dict({"version": 1, "vars": {}})
        assert e.label is None


class TestVersionResult:
    def test_repr(self):
        r = VersionResult()
        assert "versions=0" in repr(r)

    def test_latest_returns_highest_version(self):
        entries = [
            VersionEntry(version=1, vars={"A": "1"}),
            VersionEntry(version=3, vars={"A": "3"}),
            VersionEntry(version=2, vars={"A": "2"}),
        ]
        result = VersionResult(entries=entries)
        assert result.latest.version == 3

    def test_latest_returns_none_when_empty(self):
        assert VersionResult().latest is None

    def test_count(self):
        entries = [VersionEntry(version=i, vars={}) for i in range(4)]
        assert VersionResult(entries=entries).count == 4


class TestEnvVersionManager:
    def test_save_increments_version(self, manager, sample_vars):
        e1 = manager.save(sample_vars)
        e2 = manager.save(sample_vars)
        assert e1.version == 1
        assert e2.version == 2

    def test_save_with_label(self, manager, sample_vars):
        entry = manager.save(sample_vars, label="v1.0")
        assert entry.label == "v1.0"

    def test_get_returns_correct_entry(self, manager, sample_vars):
        manager.save(sample_vars)
        manager.save({"X": "1"})
        entry = manager.get(2)
        assert entry is not None
        assert entry.vars == {"X": "1"}

    def test_get_returns_none_for_missing(self, manager):
        assert manager.get(99) is None

    def test_list_returns_all_entries(self, manager, sample_vars):
        manager.save(sample_vars)
        manager.save(sample_vars)
        result = manager.list()
        assert result.count == 2

    def test_rollback_returns_vars(self, manager, sample_vars):
        manager.save(sample_vars)
        vars_ = manager.rollback(1)
        assert vars_ == sample_vars

    def test_rollback_returns_none_for_missing(self, manager):
        assert manager.rollback(42) is None

    def test_max_versions_enforced(self):
        mgr = EnvVersionManager(max_versions=3)
        for i in range(5):
            mgr.save({"K": str(i)})
        result = mgr.list()
        assert result.count == 3
        assert result.entries[0].version == 3
