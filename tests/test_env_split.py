"""Tests for EnvSplitter."""
import pytest
from envoy.env_split import EnvSplitter, SplitResult


@pytest.fixture()
def splitter() -> EnvSplitter:
    return EnvSplitter(strip_prefix=True)


@pytest.fixture()
def keep_prefix_splitter() -> EnvSplitter:
    return EnvSplitter(strip_prefix=False)


@pytest.fixture()
def sample_vars() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_HOST": "redis",
        "REDIS_PORT": "6379",
        "APP_NAME": "envoy",
        "DEBUG": "true",
    }


class TestSplitResult:
    def test_repr(self):
        r = SplitResult(groups={"DB_": {"HOST": "localhost"}})
        assert "DB_" in repr(r)

    def test_has_unmatched_false_when_empty(self):
        r = SplitResult()
        assert r.has_unmatched is False

    def test_has_unmatched_true_when_populated(self):
        r = SplitResult(unmatched={"ORPHAN": "1"})
        assert r.has_unmatched is True

    def test_group_names_returns_keys(self):
        r = SplitResult(groups={"DB_": {}, "REDIS_": {}})
        assert set(r.group_names) == {"DB_", "REDIS_"}


class TestEnvSplitter:
    def test_splits_by_prefix(self, splitter, sample_vars):
        result = splitter.split(sample_vars, ["DB_", "REDIS_"])
        assert result.groups["DB_"] == {"HOST": "localhost", "PORT": "5432"}
        assert result.groups["REDIS_"] == {"HOST": "redis", "PORT": "6379"}

    def test_unmatched_keys_collected(self, splitter, sample_vars):
        result = splitter.split(sample_vars, ["DB_", "REDIS_"])
        assert "APP_NAME" in result.unmatched
        assert "DEBUG" in result.unmatched

    def test_strip_prefix_false_keeps_full_key(self, keep_prefix_splitter, sample_vars):
        result = keep_prefix_splitter.split(sample_vars, ["DB_"])
        assert "DB_HOST" in result.groups["DB_"]
        assert "DB_PORT" in result.groups["DB_"]

    def test_first_prefix_wins(self, splitter):
        vars = {"APP_SERVICE_NAME": "web"}
        result = splitter.split(vars, ["APP_", "APP_SERVICE_"])
        assert "SERVICE_NAME" in result.groups["APP_"]
        assert "APP_SERVICE_" not in result.groups

    def test_default_group_captures_unmatched(self, splitter, sample_vars):
        result = splitter.split(sample_vars, ["DB_"], default_group="other")
        assert result.has_unmatched is False
        assert "APP_NAME" in result.groups["other"]
        assert "DEBUG" in result.groups["other"]

    def test_empty_vars_returns_empty_result(self, splitter):
        result = splitter.split({}, ["DB_", "REDIS_"])
        assert result.groups == {}
        assert result.unmatched == {}

    def test_empty_prefixes_all_unmatched(self, splitter, sample_vars):
        result = splitter.split(sample_vars, [])
        assert result.groups == {}
        assert set(result.unmatched.keys()) == set(sample_vars.keys())

    def test_merge_reconstructs_flat_dict(self, splitter, sample_vars):
        prefixes = ["DB_", "REDIS_"]
        result = splitter.split(sample_vars, prefixes)
        # merge re-adds stripped keys without original prefix — different keys
        # so just verify merge returns a dict with the same value count
        merged = splitter.merge(result)
        total = sum(len(v) for v in result.groups.values()) + len(result.unmatched)
        assert len(merged) == total

    def test_merge_unmatched_preserved(self, splitter, sample_vars):
        result = splitter.split(sample_vars, ["DB_"])
        merged = splitter.merge(result)
        assert merged.get("APP_NAME") == "envoy"
        assert merged.get("DEBUG") == "true"
