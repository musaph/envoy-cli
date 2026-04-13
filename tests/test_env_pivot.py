"""Tests for EnvPivoter."""
import pytest
from envoy.env_pivot import EnvPivoter, PivotChange, PivotResult


@pytest.fixture
def pivoter():
    return EnvPivoter()


@pytest.fixture
def overwrite_pivoter():
    return EnvPivoter(on_collision="overwrite")


@pytest.fixture
def sample_vars():
    return {"HOST": "localhost", "PORT": "8080", "ENV": "production"}


class TestPivotResult:
    def test_repr(self):
        r = PivotResult(changes=[PivotChange("K", "V", "V", "K")], collisions=["X"])
        assert "changes=1" in repr(r)
        assert "collisions=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        assert not PivotResult().has_changes

    def test_has_changes_true_when_populated(self):
        r = PivotResult(changes=[PivotChange("A", "B", "B", "A")])
        assert r.has_changes

    def test_has_collisions_false_when_empty(self):
        assert not PivotResult().has_collisions

    def test_has_collisions_true_when_populated(self):
        r = PivotResult(collisions=["dup"])
        assert r.has_collisions


class TestPivotChange:
    def test_repr_contains_keys(self):
        c = PivotChange("HOST", "localhost", "localhost", "HOST")
        assert "HOST" in repr(c)
        assert "localhost" in repr(c)


class TestEnvPivoter:
    def test_pivot_swaps_keys_and_values(self, pivoter, sample_vars):
        result = pivoter.pivot(sample_vars)
        assert result.pivoted["localhost"] == "HOST"
        assert result.pivoted["8080"] == "PORT"
        assert result.pivoted["production"] == "ENV"

    def test_pivot_records_changes(self, pivoter, sample_vars):
        result = pivoter.pivot(sample_vars)
        assert len(result.changes) == 3

    def test_empty_value_skipped_by_default(self, pivoter):
        result = pivoter.pivot({"KEY": "", "OTHER": "val"})
        assert "KEY" in result.skipped
        assert "" not in result.pivoted

    def test_empty_value_included_when_flag_set(self):
        p = EnvPivoter(skip_empty=False)
        result = p.pivot({"KEY": ""})
        assert "" in result.pivoted
        assert result.pivoted[""] == "KEY"

    def test_collision_skips_second_by_default(self):
        p = EnvPivoter(on_collision="skip")
        result = p.pivot({"A": "same", "B": "same"})
        assert "same" in result.collisions
        assert result.pivoted["same"] == "A"  # first wins

    def test_collision_overwrites_when_configured(self, overwrite_pivoter):
        result = overwrite_pivoter.pivot({"A": "same", "B": "same"})
        assert result.pivoted["same"] == "B"  # last wins

    def test_empty_input_returns_empty_result(self, pivoter):
        result = pivoter.pivot({})
        assert not result.has_changes
        assert result.pivoted == {}

    def test_no_collisions_for_unique_values(self, pivoter, sample_vars):
        result = pivoter.pivot(sample_vars)
        assert not result.has_collisions
