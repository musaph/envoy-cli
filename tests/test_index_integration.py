"""Integration tests: EnvIndexer with EnvParser and EnvExporter."""
import pytest
from envoy.parser import EnvParser
from envoy.env_index import EnvIndexer
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def indexer():
    return EnvIndexer()


@pytest.fixture
def exporter():
    return EnvExporter()


@pytest.fixture
def sample_env_content():
    return (
        "# Database\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "\n"
        "# App\n"
        "APP_NAME=envoy\n"
        "APP_DEBUG=true\n"
        "SECRET_TOKEN=\n"
    )


class TestIndexWithParser:
    def test_parse_then_index_all_keys(self, parser, indexer, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        result = indexer.build(vars_)
        assert set(result.keys) == {"DB_HOST", "DB_PORT", "APP_NAME", "APP_DEBUG", "SECRET_TOKEN"}

    def test_parse_then_index_detects_empty(self, parser, indexer, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        result = indexer.build(vars_)
        assert "SECRET_TOKEN" in result.empty_keys
        assert len(result.empty_keys) == 1

    def test_prefix_grouping_matches_expected(self, parser, indexer, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        result = indexer.build(vars_)
        db_entries = result.by_prefix("DB")
        app_entries = result.by_prefix("APP")
        assert len(db_entries) == 2
        assert len(app_entries) == 2

    def test_positions_reflect_parse_order(self, parser, indexer, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        result = indexer.build(vars_)
        keys_in_order = list(vars_.keys())
        for entry in result.entries:
            assert entry.key == keys_in_order[entry.position]

    def test_to_dict_roundtrip_for_all_entries(self, parser, indexer, sample_env_content):
        from envoy.env_index import IndexEntry
        vars_ = parser.parse(sample_env_content)
        result = indexer.build(vars_)
        for entry in result.entries:
            restored = IndexEntry.from_dict(entry.to_dict())
            assert restored.key == entry.key
            assert restored.position == entry.position
            assert restored.is_empty == entry.is_empty
