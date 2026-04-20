"""Tests for EnvSwapper."""
import pytest
from envoy.env_swap import EnvSwapper, SwapResult, SwapChange


@pytest.fixture
def swapper() -> EnvSwapper:
    return EnvSwapper()


@pytest.fixture
def overwrite_swapper() -> EnvSwapper:
    return EnvSwapper(overwrite=True)


@pytest.fixture
def sample_vars():
    return {"HOST": "localhost", "PORT": "5432", "ENV": "production"}


class TestSwapResult:
    def test_repr(self):
        r = SwapResult()
        assert "SwapResult" in repr(r)
        assert "changes=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = SwapResult()
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = SwapResult(changes=[SwapChange("A", "B", "B", "A")])
        assert r.has_changes

    def test_changed_keys(self):
        r = SwapResult(changes=[SwapChange("K", "V", "V", "K")])
        assert r.changed_keys == ["K"]


class TestSwapChange:
    def test_repr_contains_keys(self):
        c = SwapChange("HOST", "localhost", "localhost", "HOST")
        assert "HOST" in repr(c)
        assert "localhost" in repr(c)


class TestEnvSwapper:
    def test_swap_basic(self, swapper, sample_vars):
        result = swapper.swap(sample_vars)
        assert result.has_changes
        assert result.vars["localhost"] == "HOST"
        assert result.vars["5432"] == "PORT"
        assert result.vars["production"] == "ENV"

    def test_swap_empty_dict(self, swapper):
        result = swapper.swap({})
        assert not result.has_changes
        assert result.vars == {}

    def test_empty_value_is_skipped(self, swapper):
        result = swapper.swap({"EMPTY": "", "NAME": "alice"})
        assert "EMPTY" in result.skipped
        assert "alice" in result.vars

    def test_collision_skipped_without_overwrite(self, swapper):
        # Both A and B have value "same" — second one should be skipped
        result = swapper.swap({"A": "same", "B": "same"})
        assert len(result.skipped) == 1
        assert result.vars["same"] in ("A", "B")

    def test_collision_overwritten_with_overwrite(self, overwrite_swapper):
        result = overwrite_swapper.swap({"A": "same", "B": "same"})
        assert result.vars["same"] == "B"
        assert not result.skipped

    def test_single_pair(self, swapper):
        result = swapper.swap({"FOO": "bar"})
        assert result.vars == {"bar": "FOO"}
        assert len(result.changes) == 1

    def test_change_count_matches_output_vars(self, swapper, sample_vars):
        result = swapper.swap(sample_vars)
        assert len(result.changes) == len(result.vars)
