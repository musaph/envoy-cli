import pytest
from envoy.env_unique import EnvUniqueFilter, UniqueChange, UniqueResult


@pytest.fixture
def filter_cs():
    return EnvUniqueFilter(case_sensitive=True)


@pytest.fixture
def filter_ci():
    return EnvUniqueFilter(case_sensitive=False)


@pytest.fixture
def sample_vars():
    return {
        "HOST": "localhost",
        "DB_HOST": "localhost",
        "PORT": "5432",
        "DB_PORT": "5432",
        "NAME": "myapp",
    }


class TestUniqueResult:
    def test_repr(self):
        r = UniqueResult(original={"A": "1", "B": "1"}, deduped={"A": "1"}, changes=[UniqueChange("B", 1)])
        assert "UniqueResult" in repr(r)
        assert "removed=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = UniqueResult(original={}, deduped={}, changes=[])
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = UniqueResult(original={"A": "1", "B": "1"}, deduped={"A": "1"}, changes=[UniqueChange("B", 1)])
        assert r.has_changes

    def test_removed_count(self):
        r = UniqueResult(original={"A": "1", "B": "1", "C": "2"}, deduped={"A": "1", "C": "2"}, changes=[UniqueChange("B", 1)])
        assert r.removed_count == 1

    def test_duplicate_keys(self):
        r = UniqueResult(original={}, deduped={}, changes=[UniqueChange("X", 2), UniqueChange("Y", 1)])
        assert r.duplicate_keys == ["X", "Y"]


class TestEnvUniqueFilter:
    def test_no_duplicates_unchanged(self, filter_cs):
        vars = {"A": "1", "B": "2", "C": "3"}
        result = filter_cs.filter(vars)
        assert not result.has_changes
        assert result.deduped == vars

    def test_removes_duplicate_values(self, filter_cs, sample_vars):
        result = filter_cs.filter(sample_vars)
        assert result.has_changes
        assert "HOST" in result.deduped
        assert "DB_HOST" not in result.deduped
        assert "PORT" in result.deduped
        assert "DB_PORT" not in result.deduped
        assert "NAME" in result.deduped

    def test_keeps_first_occurrence(self, filter_cs):
        vars = {"FIRST": "same", "SECOND": "same", "THIRD": "same"}
        result = filter_cs.filter(vars)
        assert "FIRST" in result.deduped
        assert "SECOND" not in result.deduped
        assert "THIRD" not in result.deduped

    def test_case_sensitive_treats_differently(self, filter_cs):
        vars = {"A": "Value", "B": "value"}
        result = filter_cs.filter(vars)
        assert not result.has_changes
        assert len(result.deduped) == 2

    def test_case_insensitive_merges(self, filter_ci):
        vars = {"A": "Value", "B": "value"}
        result = filter_ci.filter(vars)
        assert result.has_changes
        assert len(result.deduped) == 1

    def test_empty_vars(self, filter_cs):
        result = filter_cs.filter({})
        assert not result.has_changes
        assert result.deduped == {}
        assert result.removed_count == 0
