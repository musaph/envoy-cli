"""Tests for EnvGrouper."""
import pytest
from envoy.env_group import EnvGrouper, GroupResult


@pytest.fixture
def grouper() -> EnvGrouper:
    return EnvGrouper(min_group_size=2)


@pytest.fixture
def sample_vars() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "mydb",
        "AWS_ACCESS_KEY": "AKIA123",
        "AWS_SECRET_KEY": "secret",
        "APP_ENV": "production",
        "DEBUG": "false",
    }


class TestGroupResult:
    def test_repr(self):
        r = GroupResult(groups={"DB": {"DB_HOST": "x"}}, ungrouped={"X": "y"})
        assert "groups=1" in repr(r)
        assert "ungrouped=1" in repr(r)

    def test_all_vars_combines_everything(self):
        r = GroupResult(
            groups={"DB": {"DB_HOST": "localhost"}},
            ungrouped={"DEBUG": "true"},
        )
        all_ = r.all_vars
        assert all_["DB_HOST"] == "localhost"
        assert all_["DEBUG"] == "true"

    def test_all_vars_empty(self):
        r = GroupResult()
        assert r.all_vars == {}


class TestEnvGrouper:
    def test_group_by_explicit_prefixes(self, grouper, sample_vars):
        result = grouper.group_by_prefix(sample_vars, prefixes=["DB", "AWS"])
        assert "DB" in result.groups
        assert "AWS" in result.groups
        assert len(result.groups["DB"]) == 3
        assert len(result.groups["AWS"]) == 2

    def test_ungrouped_contains_remainder(self, grouper, sample_vars):
        result = grouper.group_by_prefix(sample_vars, prefixes=["DB"])
        assert "DEBUG" in result.ungrouped
        assert "APP_ENV" in result.ungrouped
        assert "AWS_ACCESS_KEY" in result.ungrouped

    def test_auto_detect_prefixes(self, sample_vars):
        g = EnvGrouper(min_group_size=2)
        result = g.group_by_prefix(sample_vars)
        assert "DB" in result.groups
        assert "AWS" in result.groups

    def test_min_group_size_filters_small_groups(self, sample_vars):
        # APP_ only has one key, should not be auto-detected with min=2
        g = EnvGrouper(min_group_size=2)
        result = g.group_by_prefix(sample_vars)
        assert "APP" not in result.groups
        assert "APP_ENV" in result.ungrouped

    def test_empty_vars_returns_empty_result(self, grouper):
        result = grouper.group_by_prefix({})
        assert result.groups == {}
        assert result.ungrouped == {}

    def test_no_prefixed_vars_all_ungrouped(self, grouper):
        vars_ = {"FOO": "1", "BAR": "2"}
        result = grouper.group_by_prefix(vars_, prefixes=["DB"])
        assert result.groups == {}
        assert result.ungrouped == {"FOO": "1", "BAR": "2"}

    def test_custom_separator(self):
        g = EnvGrouper(min_group_size=1, separator=".")
        vars_ = {"db.host": "localhost", "db.port": "5432", "debug": "true"}
        result = g.group_by_prefix(vars_, prefixes=["db"])
        assert "db" in result.groups
        assert "debug" in result.ungrouped
