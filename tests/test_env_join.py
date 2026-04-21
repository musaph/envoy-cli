"""Tests for EnvJoiner."""
import pytest
from envoy.env_join import EnvJoiner, JoinResult, JoinChange


@pytest.fixture
def joiner() -> EnvJoiner:
    return EnvJoiner(separator=",")


@pytest.fixture
def overwrite_joiner() -> EnvJoiner:
    return EnvJoiner(separator=",", overwrite=True)


@pytest.fixture
def sample_a() -> dict:
    return {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}


@pytest.fixture
def sample_b() -> dict:
    return {"HOST": "remotehost", "PORT": "5433", "USER": "admin"}


class TestJoinResult:
    def test_repr(self):
        r = JoinResult(vars={"A": "1"}, changes=[], skipped=[])
        assert "JoinResult" in repr(r)
        assert "total=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = JoinResult()
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = JoinResult(changes=[JoinChange(key="X", sources=["a", "b"], value="1,2")])
        assert r.has_changes

    def test_changed_keys(self):
        r = JoinResult(changes=[JoinChange(key="HOST", sources=["a", "b"], value="x,y")])
        assert r.changed_keys == ["HOST"]


class TestEnvJoiner:
    def test_single_source_no_changes(self, joiner, sample_a):
        result = joiner.join([sample_a])
        assert result.vars == sample_a
        assert not result.has_changes

    def test_disjoint_sources_merged(self, joiner):
        a = {"A": "1"}
        b = {"B": "2"}
        result = joiner.join([a, b])
        assert result.vars == {"A": "1", "B": "2"}
        assert not result.has_changes

    def test_overlapping_keys_joined_with_separator(self, joiner, sample_a, sample_b):
        result = joiner.join([sample_a, sample_b])
        assert result.vars["HOST"] == "localhost,remotehost"
        assert result.vars["PORT"] == "5432,5433"
        assert result.vars["DEBUG"] == "true"
        assert result.vars["USER"] == "admin"

    def test_overlapping_keys_recorded_as_changes(self, joiner, sample_a, sample_b):
        result = joiner.join([sample_a, sample_b])
        assert result.has_changes
        changed = {c.key for c in result.changes}
        assert "HOST" in changed
        assert "PORT" in changed
        assert "DEBUG" not in changed

    def test_overwrite_mode_last_wins(self, overwrite_joiner, sample_a, sample_b):
        result = overwrite_joiner.join([sample_a, sample_b])
        assert result.vars["HOST"] == "remotehost"
        assert result.vars["PORT"] == "5433"

    def test_custom_separator(self, sample_a, sample_b):
        j = EnvJoiner(separator=" | ")
        result = j.join([sample_a, sample_b])
        assert result.vars["HOST"] == "localhost | remotehost"

    def test_source_names_recorded_in_changes(self, joiner, sample_a, sample_b):
        result = joiner.join([sample_a, sample_b], source_names=["dev", "prod"])
        host_change = next(c for c in result.changes if c.key == "HOST")
        assert host_change.sources == ["dev", "prod"]

    def test_auto_source_names_generated(self, joiner, sample_a, sample_b):
        result = joiner.join([sample_a, sample_b])
        host_change = next(c for c in result.changes if c.key == "HOST")
        assert host_change.sources == ["source_0", "source_1"]

    def test_empty_sources_returns_empty(self, joiner):
        result = joiner.join([])
        assert result.vars == {}
        assert not result.has_changes

    def test_join_change_repr(self):
        c = JoinChange(key="K", sources=["a", "b"], value="x,y")
        assert "JoinChange" in repr(c)
        assert "K" in repr(c)
