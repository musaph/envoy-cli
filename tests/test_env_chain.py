"""Tests for EnvChainer."""
import pytest
from envoy.env_chain import ChainEntry, ChainResult, EnvChainer


@pytest.fixture
def chainer() -> EnvChainer:
    return EnvChainer()


class TestChainResult:
    def test_repr(self):
        r = ChainResult(
            merged={"A": "1"},
            entries=[ChainEntry("base", "A", "1", overridden_by="override")],
            sources=["base", "override"],
        )
        assert "sources=2" in repr(r)
        assert "keys=1" in repr(r)
        assert "overrides=1" in repr(r)

    def test_overridden_entries_filtered(self):
        e1 = ChainEntry("base", "A", "1", overridden_by="prod")
        e2 = ChainEntry("prod", "A", "2")
        r = ChainResult(merged={"A": "2"}, entries=[e1, e2], sources=["base", "prod"])
        assert len(r.overridden_entries) == 1
        assert r.overridden_entries[0].source == "base"


class TestChainEntry:
    def test_repr_no_override(self):
        e = ChainEntry("base", "KEY", "val")
        assert "base:KEY" in repr(e)
        assert "overridden" not in repr(e)

    def test_repr_with_override(self):
        e = ChainEntry("base", "KEY", "val", overridden_by="prod")
        assert "overridden by prod" in repr(e)


class TestEnvChainer:
    def test_single_source(self, chainer):
        result = chainer.chain([("base", {"A": "1", "B": "2"})])
        assert result.merged == {"A": "1", "B": "2"}
        assert result.sources == ["base"]
        assert len(result.overridden_entries) == 0

    def test_later_source_overrides(self, chainer):
        result = chainer.chain([
            ("base", {"A": "1", "B": "2"}),
            ("prod", {"A": "99"}),
        ])
        assert result.merged["A"] == "99"
        assert result.merged["B"] == "2"

    def test_override_recorded(self, chainer):
        result = chainer.chain([
            ("base", {"X": "old"}),
            ("prod", {"X": "new"}),
        ])
        overrides = result.overridden_entries
        assert len(overrides) == 1
        assert overrides[0].key == "X"
        assert overrides[0].overridden_by == "prod"

    def test_three_sources_last_wins(self, chainer):
        result = chainer.chain([
            ("a", {"K": "1"}),
            ("b", {"K": "2"}),
            ("c", {"K": "3"}),
        ])
        assert result.merged["K"] == "3"

    def test_empty_sources(self, chainer):
        result = chainer.chain([])
        assert result.merged == {}
        assert result.sources == []

    def test_no_overlap_no_overrides(self, chainer):
        result = chainer.chain([
            ("base", {"A": "1"}),
            ("extra", {"B": "2"}),
        ])
        assert result.merged == {"A": "1", "B": "2"}
        assert len(result.overridden_entries) == 0

    def test_sources_list_preserved(self, chainer):
        result = chainer.chain([("x", {}), ("y", {})])
        assert result.sources == ["x", "y"]
