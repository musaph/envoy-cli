"""Integration tests: EnvChainer with EnvParser and EnvSorter."""
import pytest
from envoy.env_chain import EnvChainer
from envoy.parser import EnvParser
from envoy.env_sort import EnvSorter, SortOrder


@pytest.fixture
def parser() -> EnvParser:
    return EnvParser()


@pytest.fixture
def chainer() -> EnvChainer:
    return EnvChainer()


@pytest.fixture
def sorter() -> EnvSorter:
    return EnvSorter()


class TestChainWithParser:
    def test_parse_then_chain_merges_correctly(self, parser, chainer):
        base = parser.parse("DB_HOST=localhost\nDB_PORT=5432\n")
        override = parser.parse("DB_HOST=prod.db\nDB_PASS=secret\n")
        result = chainer.chain([("base", base), ("override", override)])
        assert result.merged["DB_HOST"] == "prod.db"
        assert result.merged["DB_PORT"] == "5432"
        assert result.merged["DB_PASS"] == "secret"

    def test_chain_then_sort_produces_ordered_output(self, parser, chainer, sorter):
        a = parser.parse("Z_KEY=z\nA_KEY=a\n")
        b = parser.parse("M_KEY=m\n")
        chain_result = chainer.chain([("a", a), ("b", b)])
        sort_result = sorter.sort(chain_result.merged, order=SortOrder.ASC)
        keys = list(sort_result.sorted_vars.keys())
        assert keys == sorted(keys)

    def test_three_layer_chain_last_wins(self, parser, chainer):
        dev = parser.parse("ENV=dev\nFEATURE=off\n")
        staging = parser.parse("ENV=staging\n")
        prod = parser.parse("ENV=prod\nFEATURE=on\n")
        result = chainer.chain([("dev", dev), ("staging", staging), ("prod", prod)])
        assert result.merged["ENV"] == "prod"
        assert result.merged["FEATURE"] == "on"
        assert len(result.overridden_entries) >= 2

    def test_empty_override_does_not_remove_keys(self, parser, chainer):
        base = parser.parse("A=1\nB=2\n")
        empty = parser.parse("")
        result = chainer.chain([("base", base), ("empty", empty)])
        assert result.merged == {"A": "1", "B": "2"}
