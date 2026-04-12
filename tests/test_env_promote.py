"""Tests for EnvPromoter and PromoteResult."""
import pytest
from envoy.env_promote import EnvPromoter, PromoteResult, PromoteChange


@pytest.fixture
def promoter():
    return EnvPromoter()


@pytest.fixture
def overwrite_promoter():
    return EnvPromoter(overwrite=True)


class TestPromoteResult:
    def test_repr(self):
        r = PromoteResult()
        assert "added=0" in repr(r)
        assert "overwritten=0" in repr(r)
        assert "skipped=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = PromoteResult()
        assert not r.has_changes

    def test_has_changes_true_when_added(self):
        r = PromoteResult(added=[PromoteChange("K", "v", None)])
        assert r.has_changes

    def test_has_changes_true_when_overwritten(self):
        r = PromoteResult(overwritten=[PromoteChange("K", "v", "old", overwritten=True)])
        assert r.has_changes


class TestPromoteChange:
    def test_repr_add(self):
        c = PromoteChange(key="FOO", source_value="bar", target_value=None)
        assert "add" in repr(c)
        assert "FOO" in repr(c)

    def test_repr_overwrite(self):
        c = PromoteChange(key="FOO", source_value="new", target_value="old", overwritten=True)
        assert "overwrite" in repr(c)


class TestEnvPromoter:
    def test_adds_new_keys(self, promoter):
        source = {"A": "1", "B": "2"}
        target = {}
        result, merged = promoter.promote(source, target)
        assert len(result.added) == 2
        assert merged["A"] == "1"
        assert merged["B"] == "2"

    def test_skips_existing_keys_without_overwrite(self, promoter):
        source = {"A": "new"}
        target = {"A": "old"}
        result, merged = promoter.promote(source, target)
        assert len(result.skipped) == 1
        assert "A" in result.skipped
        assert merged["A"] == "old"

    def test_overwrites_existing_keys_when_flag_set(self, overwrite_promoter):
        source = {"A": "new"}
        target = {"A": "old"}
        result, merged = overwrite_promoter.promote(source, target)
        assert len(result.overwritten) == 1
        assert merged["A"] == "new"

    def test_keys_allowlist_filters_promotion(self):
        p = EnvPromoter(keys=["A"])
        source = {"A": "1", "B": "2"}
        target = {}
        result, merged = p.promote(source, target)
        assert "A" in merged
        assert "B" not in merged
        assert len(result.added) == 1

    def test_target_unchanged_keys_preserved(self, promoter):
        source = {"A": "1"}
        target = {"B": "existing"}
        _, merged = promoter.promote(source, target)
        assert merged["B"] == "existing"
        assert merged["A"] == "1"

    def test_empty_source_no_changes(self, promoter):
        result, merged = promoter.promote({}, {"X": "1"})
        assert not result.has_changes
        assert merged == {"X": "1"}

    def test_overwrite_records_old_value(self, overwrite_promoter):
        source = {"KEY": "new"}
        target = {"KEY": "old"}
        result, _ = overwrite_promoter.promote(source, target)
        assert result.overwritten[0].target_value == "old"
        assert result.overwritten[0].source_value == "new"
