"""Tests for EnvMerger and MergeResult."""
import pytest
from envoy.env_merge import EnvMerger, MergeResult, MergeStrategy


@pytest.fixture
def merger():
    return EnvMerger()


class TestMergeResult:
    def test_has_conflicts_false_when_empty(self):
        r = MergeResult()
        assert not r.has_conflicts

    def test_has_conflicts_true_when_populated(self):
        r = MergeResult(conflicts={"KEY": ("a", "b")})
        assert r.has_conflicts

    def test_repr_contains_counts(self):
        r = MergeResult(merged={"A": "1"}, conflicts={"B": ("x", "y")})
        assert "merged=1" in repr(r)
        assert "conflicts=1" in repr(r)


class TestEnvMerger:
    def test_no_overlap_combines_all(self, merger):
        local = {"A": "1", "B": "2"}
        remote = {"C": "3"}
        result = merger.merge(local, remote)
        assert result.merged == {"A": "1", "B": "2", "C": "3"}
        assert not result.has_conflicts
        assert "C" in result.added_from_remote
        assert set(result.added_from_local) == {"A", "B"}

    def test_identical_values_no_conflict(self, merger):
        local = {"KEY": "value"}
        remote = {"KEY": "value"}
        result = merger.merge(local, remote)
        assert result.merged == {"KEY": "value"}
        assert not result.has_conflicts

    def test_local_wins_on_conflict(self):
        merger = EnvMerger(strategy=MergeStrategy.LOCAL_WINS)
        result = merger.merge({"KEY": "local_val"}, {"KEY": "remote_val"})
        assert result.merged["KEY"] == "local_val"
        assert result.has_conflicts

    def test_remote_wins_on_conflict(self):
        merger = EnvMerger(strategy=MergeStrategy.REMOTE_WINS)
        result = merger.merge({"KEY": "local_val"}, {"KEY": "remote_val"})
        assert result.merged["KEY"] == "remote_val"
        assert result.has_conflicts

    def test_interactive_excludes_conflict_from_merged(self):
        merger = EnvMerger(strategy=MergeStrategy.INTERACTIVE)
        result = merger.merge({"KEY": "local"}, {"KEY": "remote"})
        assert "KEY" not in result.merged
        assert result.has_conflicts

    def test_overrides_always_win(self, merger):
        local = {"KEY": "local"}
        remote = {"KEY": "remote"}
        result = merger.merge(local, remote, overrides={"KEY": "override"})
        assert result.merged["KEY"] == "override"
        assert not result.has_conflicts

    def test_override_adds_new_key(self, merger):
        result = merger.merge({}, {}, overrides={"NEW": "injected"})
        assert result.merged["NEW"] == "injected"

    def test_empty_inputs(self, merger):
        result = merger.merge({}, {})
        assert result.merged == {}
        assert not result.has_conflicts

    def test_multiple_conflicts_tracked(self):
        merger = EnvMerger(strategy=MergeStrategy.LOCAL_WINS)
        local = {"A": "1", "B": "2"}
        remote = {"A": "x", "B": "y"}
        result = merger.merge(local, remote)
        assert len(result.conflicts) == 2
        assert result.conflicts["A"] == ("1", "x")
        assert result.conflicts["B"] == ("2", "y")
