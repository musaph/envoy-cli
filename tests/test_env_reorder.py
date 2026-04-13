import pytest
from envoy.env_reorder import EnvReorderer, ReorderChange, ReorderResult


@pytest.fixture
def reorderer():
    return EnvReorderer(alphabetical=True)


@pytest.fixture
def sample_vars():
    return {"ZEBRA": "1", "APPLE": "2", "MANGO": "3"}


class TestReorderResult:
    def test_repr(self):
        r = ReorderResult(original={}, reordered={}, changes=[ReorderChange("A", 0, 1)])
        assert "ReorderResult" in repr(r)
        assert "1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = ReorderResult(original={}, reordered={}, changes=[])
        assert r.has_changes is False

    def test_has_changes_true_when_populated(self):
        r = ReorderResult(
            original={}, reordered={}, changes=[ReorderChange("X", 2, 0)]
        )
        assert r.has_changes is True


class TestReorderChange:
    def test_repr_contains_key_and_indices(self):
        ch = ReorderChange(key="FOO", old_index=3, new_index=0)
        r = repr(ch)
        assert "FOO" in r
        assert "3" in r
        assert "0" in r


class TestEnvReorderer:
    def test_alphabetical_sorts_correctly(self, reorderer, sample_vars):
        result = reorderer.reorder(sample_vars)
        assert list(result.reordered.keys()) == ["APPLE", "MANGO", "ZEBRA"]

    def test_alphabetical_detects_changes(self, reorderer, sample_vars):
        result = reorderer.reorder(sample_vars)
        assert result.has_changes

    def test_already_sorted_no_changes(self):
        r = EnvReorderer(alphabetical=True)
        vars_ = {"A": "1", "B": "2", "C": "3"}
        result = r.reorder(vars_)
        assert not result.has_changes
        assert list(result.reordered.keys()) == ["A", "B", "C"]

    def test_explicit_order_respected(self, sample_vars):
        r = EnvReorderer(order=["MANGO", "ZEBRA", "APPLE"])
        result = r.reorder(sample_vars)
        assert list(result.reordered.keys()) == ["MANGO", "ZEBRA", "APPLE"]

    def test_explicit_order_appends_unknown_keys(self):
        r = EnvReorderer(order=["B"])
        vars_ = {"A": "1", "B": "2", "C": "3"}
        result = r.reorder(vars_)
        assert list(result.reordered.keys())[0] == "B"
        assert set(result.reordered.keys()) == {"A", "B", "C"}

    def test_no_order_no_alphabetical_returns_unchanged(self, sample_vars):
        r = EnvReorderer()
        result = r.reorder(sample_vars)
        assert not result.has_changes
        assert list(result.reordered.keys()) == list(sample_vars.keys())

    def test_values_preserved_after_reorder(self, reorderer, sample_vars):
        result = reorderer.reorder(sample_vars)
        for k, v in sample_vars.items():
            assert result.reordered[k] == v
