import pytest
from envoy.env_version import EnvVersionManager
from envoy.parser import EnvParser
from envoy.env_diff_summary import EnvDiffSummarizer


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def manager():
    return EnvVersionManager(max_versions=10)


class TestVersionWithParser:
    def test_parse_then_save_version(self, parser, manager):
        content = "APP=prod\nDB=postgres\nPORT=5432\n"
        vars_ = parser.parse(content)
        entry = manager.save(vars_, label="initial")
        assert entry.version == 1
        assert entry.vars["APP"] == "prod"
        assert entry.label == "initial"

    def test_multiple_versions_preserve_history(self, parser, manager):
        v1_content = "APP=staging\nDB=sqlite\n"
        v2_content = "APP=production\nDB=postgres\nREDIS=localhost\n"
        manager.save(parser.parse(v1_content))
        manager.save(parser.parse(v2_content))
        result = manager.list()
        assert result.count == 2
        assert result.latest.vars["DB"] == "postgres"
        assert manager.get(1).vars["DB"] == "sqlite"

    def test_rollback_then_serialize(self, parser, manager):
        original = {"APP": "v1", "SECRET": "abc"}
        manager.save(original)
        manager.save({"APP": "v2", "SECRET": "xyz", "NEW_KEY": "added"})
        rolled_back = manager.rollback(1)
        assert rolled_back is not None
        serialized = parser.serialize(rolled_back)
        reparsed = parser.parse(serialized)
        assert reparsed["APP"] == "v1"
        assert "NEW_KEY" not in reparsed

    def test_version_vars_are_independent_copies(self, parser, manager):
        vars_ = {"X": "original"}
        entry = manager.save(vars_)
        vars_["X"] = "mutated"
        assert entry.vars["X"] == "original"
