"""Tests for envoy.env_squash."""
import pytest
from envoy.env_squash import EnvSquasher, SquashChange, SquashResult


@pytest.fixture
def squasher() -> EnvSquasher:
    return EnvSquasher(
        alias_map={
            "DATABASE_URL": ["DB_URL", "DATABASE_URI"],
            "API_KEY": ["APIKEY", "API_TOKEN"],
        }
    )


@pytest.fixture
def prefer_last_squasher() -> EnvSquasher:
    return EnvSquasher(
        alias_map={"DATABASE_URL": ["DB_URL", "DATABASE_URI"]},
        prefer_last=True,
    )


@pytest.fixture
def sample_vars() -> dict:
    return {
        "DATABASE_URL": "postgres://original",
        "DB_URL": "postgres://alias1",
        "DATABASE_URI": "postgres://alias2",
        "API_KEY": "key-123",
        "APIKEY": "key-old",
        "OTHER": "untouched",
    }


class TestSquashResult:
    def test_repr(self):
        r = SquashResult()
        assert "SquashResult" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = SquashResult()
        assert r.has_changes() is False

    def test_has_changes_true_when_populated(self):
        c = SquashChange(canonical="K", absorbed=["K2"], chosen_value="v")
        r = SquashResult(changes=[c])
        assert r.has_changes() is True

    def test_absorbed_keys_aggregates_all(self):
        c1 = SquashChange(canonical="A", absorbed=["A1", "A2"], chosen_value="v")
        c2 = SquashChange(canonical="B", absorbed=["B1"], chosen_value="w")
        r = SquashResult(changes=[c1, c2])
        assert set(r.absorbed_keys()) == {"A1", "A2", "B1"}

    def test_absorbed_keys_empty_when_no_changes(self):
        assert SquashResult().absorbed_keys() == []


class TestEnvSquasher:
    def test_no_alias_map_returns_unchanged(self, sample_vars):
        result = EnvSquasher().squash(sample_vars)
        assert result.output == sample_vars
        assert result.has_changes() is False

    def test_aliases_removed_from_output(self, squasher, sample_vars):
        result = squasher.squash(sample_vars)
        assert "DB_URL" not in result.output
        assert "DATABASE_URI" not in result.output
        assert "APIKEY" not in result.output

    def test_canonical_key_preserved(self, squasher, sample_vars):
        result = squasher.squash(sample_vars)
        assert "DATABASE_URL" in result.output
        assert "API_KEY" in result.output

    def test_prefer_first_keeps_canonical_value(self, squasher, sample_vars):
        result = squasher.squash(sample_vars)
        assert result.output["DATABASE_URL"] == "postgres://original"

    def test_prefer_last_keeps_last_alias_value(self, prefer_last_squasher, sample_vars):
        result = prefer_last_squasher.squash(sample_vars)
        assert result.output["DATABASE_URL"] == "postgres://alias2"

    def test_unrelated_keys_untouched(self, squasher, sample_vars):
        result = squasher.squash(sample_vars)
        assert result.output["OTHER"] == "untouched"

    def test_no_aliases_present_skips_canonical(self, squasher):
        vars = {"UNRELATED": "value"}
        result = squasher.squash(vars)
        assert result.output == vars
        assert not result.has_changes()

    def test_change_records_correct_absorbed(self, squasher, sample_vars):
        result = squasher.squash(sample_vars)
        db_change = next(c for c in result.changes if c.canonical == "DATABASE_URL")
        assert set(db_change.absorbed) == {"DB_URL", "DATABASE_URI"}

    def test_partial_aliases_only_removes_present(self, squasher):
        vars = {"DB_URL": "postgres://only-alias", "OTHER": "x"}
        result = squasher.squash(vars)
        assert "DATABASE_URL" in result.output
        assert "DB_URL" not in result.output
        assert result.output["DATABASE_URL"] == "postgres://only-alias"
