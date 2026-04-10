"""Tests for envoy.env_sort module."""
import pytest

from envoy.env_sort import EnvSorter, GroupBy, SortOrder, SortResult


@pytest.fixture()
def sorter() -> EnvSorter:
    return EnvSorter()


@pytest.fixture()
def sample_vars() -> dict:
    return {
        "ZEBRA": "last",
        "APP_NAME": "myapp",
        "APP_PORT": "8080",
        "DB_HOST": "localhost",
        "DB_PASS": "secret",
        "LOG_LEVEL": "info",
    }


class TestSortResult:
    def test_repr(self):
        r = SortResult(sorted_vars={"A": "1"}, original_count=1, sorted_count=1)
        assert "SortResult" in repr(r)

    def test_defaults(self):
        r = SortResult(sorted_vars={})
        assert r.groups == {}
        assert r.original_count == 0


class TestEnvSorterAscending:
    def test_sort_returns_sort_result(self, sorter, sample_vars):
        result = sorter.sort(sample_vars)
        assert isinstance(result, SortResult)

    def test_sorted_count_matches_input(self, sorter, sample_vars):
        result = sorter.sort(sample_vars)
        assert result.sorted_count == len(sample_vars)
        assert result.original_count == len(sample_vars)

    def test_keys_are_ascending(self, sorter, sample_vars):
        result = sorter.sort(sample_vars)
        keys = list(result.sorted_vars.keys())
        assert keys == sorted(keys)

    def test_values_preserved(self, sorter, sample_vars):
        result = sorter.sort(sample_vars)
        for k, v in sample_vars.items():
            assert result.sorted_vars[k] == v


class TestEnvSorterDescending:
    def test_keys_are_descending(self, sample_vars):
        sorter = EnvSorter(order=SortOrder.DESC)
        result = sorter.sort(sample_vars)
        keys = list(result.sorted_vars.keys())
        assert keys == sorted(keys, reverse=True)


class TestEnvSorterGroupByPrefix:
    def test_groups_created(self, sample_vars):
        sorter = EnvSorter(group_by=GroupBy.PREFIX)
        result = sorter.sort(sample_vars)
        assert "APP" in result.groups
        assert "DB" in result.groups
        assert "LOG" in result.groups

    def test_ungrouped_keys_in_other(self):
        sorter = EnvSorter(group_by=GroupBy.PREFIX)
        result = sorter.sort({"NOUNDERSCORE": "val"})
        assert "__other__" in result.groups
        assert result.groups["__other__"]["NOUNDERSCORE"] == "val"

    def test_group_contents_correct(self, sample_vars):
        sorter = EnvSorter(group_by=GroupBy.PREFIX)
        result = sorter.sort(sample_vars)
        assert "APP_NAME" in result.groups["APP"]
        assert "APP_PORT" in result.groups["APP"]
        assert "DB_HOST" in result.groups["DB"]

    def test_no_groups_when_group_by_none(self, sorter, sample_vars):
        result = sorter.sort(sample_vars)
        assert result.groups == {}


class TestSortKeysInGroup:
    def test_sort_group_ascending(self, sorter):
        group = {"Z": "1", "A": "2", "M": "3"}
        result = sorter.sort_keys_in_group(group)
        assert list(result.keys()) == ["A", "M", "Z"]

    def test_sort_group_override_desc(self, sorter):
        group = {"Z": "1", "A": "2", "M": "3"}
        result = sorter.sort_keys_in_group(group, order=SortOrder.DESC)
        assert list(result.keys()) == ["Z", "M", "A"]
