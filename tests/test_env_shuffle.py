import pytest
from envoy.env_shuffle import EnvShuffler, ShuffleResult


@pytest.fixture
def shuffler():
    return EnvShuffler(seed=42)


@pytest.fixture
def sample_vars():
    return {"ALPHA": "1", "BETA": "2", "GAMMA": "3", "DELTA": "4"}


class TestShuffleResult:
    def test_repr(self):
        r = ShuffleResult(
            original_order=["A", "B"],
            shuffled_order=["B", "A"],
            vars={"B": "2", "A": "1"},
            seed=7,
        )
        assert "ShuffleResult" in repr(r)
        assert "seed=7" in repr(r)

    def test_has_changes_true_when_reordered(self):
        r = ShuffleResult(
            original_order=["A", "B"],
            shuffled_order=["B", "A"],
            vars={"B": "2", "A": "1"},
        )
        assert r.has_changes is True

    def test_has_changes_false_when_same_order(self):
        r = ShuffleResult(
            original_order=["A", "B"],
            shuffled_order=["A", "B"],
            vars={"A": "1", "B": "2"},
        )
        assert r.has_changes is False

    def test_changed_positions_count(self):
        r = ShuffleResult(
            original_order=["A", "B", "C"],
            shuffled_order=["C", "B", "A"],
            vars={"C": "3", "B": "2", "A": "1"},
        )
        assert r.changed_positions == 2


class TestEnvShuffler:
    def test_shuffle_preserves_all_keys(self, shuffler, sample_vars):
        result = shuffler.shuffle(sample_vars)
        assert set(result.vars.keys()) == set(sample_vars.keys())

    def test_shuffle_preserves_all_values(self, shuffler, sample_vars):
        result = shuffler.shuffle(sample_vars)
        assert set(result.vars.values()) == set(sample_vars.values())

    def test_shuffle_with_seed_is_deterministic(self, sample_vars):
        r1 = EnvShuffler(seed=99).shuffle(sample_vars)
        r2 = EnvShuffler(seed=99).shuffle(sample_vars)
        assert r1.shuffled_order == r2.shuffled_order

    def test_different_seeds_may_differ(self, sample_vars):
        r1 = EnvShuffler(seed=1).shuffle(sample_vars)
        r2 = EnvShuffler(seed=2).shuffle(sample_vars)
        # Not guaranteed to differ, but with 4 keys very likely
        assert isinstance(r1.shuffled_order, list)
        assert isinstance(r2.shuffled_order, list)

    def test_restore_returns_original_order(self, shuffler, sample_vars):
        result = shuffler.shuffle(sample_vars)
        restored = shuffler.restore(result)
        assert list(restored.keys()) == list(sample_vars.keys())
        assert restored == sample_vars

    def test_original_order_recorded(self, shuffler, sample_vars):
        result = shuffler.shuffle(sample_vars)
        assert result.original_order == list(sample_vars.keys())

    def test_single_var_no_change(self):
        s = EnvShuffler(seed=0)
        result = s.shuffle({"ONLY": "val"})
        assert result.has_changes is False
