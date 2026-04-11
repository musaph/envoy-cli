"""Tests for envoy.env_dedup."""
import pytest
from envoy.env_dedup import DedupResult, EnvDeduplicator


@pytest.fixture
def deduplicator():
    return EnvDeduplicator(strategy="last")


@pytest.fixture
def first_deduplicator():
    return EnvDeduplicator(strategy="first")


# ---------------------------------------------------------------------------
# DedupResult
# ---------------------------------------------------------------------------

class TestDedupResult:
    def test_repr(self):
        r = DedupResult(
            original={"A": "1", "B": "2"},
            deduplicated={"A": "1", "B": "2"},
            duplicates={},
        )
        assert "DedupResult" in repr(r)
        assert "unique=2" in repr(r)

    def test_has_duplicates_false(self):
        r = DedupResult(original={}, deduplicated={}, duplicates={})
        assert r.has_duplicates is False

    def test_has_duplicates_true(self):
        r = DedupResult(
            original={"X": "1"},
            deduplicated={"X": "1"},
            duplicates={"X": ["1", "2"]},
        )
        assert r.has_duplicates is True

    def test_removed_count(self):
        r = DedupResult(
            original={"A": "1", "B": "2", "C": "3"},
            deduplicated={"A": "1", "B": "2"},
            duplicates={"C": ["3", "4"]},
        )
        assert r.removed_count == 1


# ---------------------------------------------------------------------------
# EnvDeduplicator — strategy validation
# ---------------------------------------------------------------------------

def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="strategy"):
        EnvDeduplicator(strategy="random")


# ---------------------------------------------------------------------------
# EnvDeduplicator.deduplicate
# ---------------------------------------------------------------------------

class TestEnvDeduplicator:
    def test_no_duplicates_unchanged(self, deduplicator):
        pairs = [("A", "1"), ("B", "2"), ("C", "3")]
        result = deduplicator.deduplicate(pairs)
        assert not result.has_duplicates
        assert result.deduplicated == {"A": "1", "B": "2", "C": "3"}

    def test_last_strategy_keeps_last(self, deduplicator):
        pairs = [("KEY", "first"), ("OTHER", "x"), ("KEY", "last")]
        result = deduplicator.deduplicate(pairs)
        assert result.deduplicated["KEY"] == "last"
        assert result.duplicates == {"KEY": ["first", "last"]}

    def test_first_strategy_keeps_first(self, first_deduplicator):
        pairs = [("KEY", "first"), ("KEY", "second"), ("KEY", "third")]
        result = first_deduplicator.deduplicate(pairs)
        assert result.deduplicated["KEY"] == "first"

    def test_multiple_duplicate_keys(self, deduplicator):
        pairs = [("A", "1"), ("B", "x"), ("A", "2"), ("B", "y")]
        result = deduplicator.deduplicate(pairs)
        assert len(result.duplicates) == 2
        assert result.deduplicated["A"] == "2"
        assert result.deduplicated["B"] == "y"

    def test_from_dict_no_duplicates(self, deduplicator):
        vars_ = {"FOO": "bar", "BAZ": "qux"}
        result = deduplicator.from_dict(vars_)
        assert not result.has_duplicates
        assert result.deduplicated == vars_

    def test_empty_input(self, deduplicator):
        result = deduplicator.deduplicate([])
        assert result.deduplicated == {}
        assert not result.has_duplicates
        assert result.removed_count == 0
