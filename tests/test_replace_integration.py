import pytest
from envoy.env_replace import EnvReplacer
from envoy.parser import EnvParser
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def replacer():
    return EnvReplacer(pattern="localhost", replacement="db.internal")


@pytest.fixture
def exporter():
    return EnvExporter()


@pytest.fixture
def sample_env_content():
    return (
        "DB_URL=postgres://localhost/mydb\n"
        "REDIS_URL=redis://localhost:6379\n"
        "APP_NAME=myapp\n"
    )


class TestReplaceWithParser:
    def test_parse_then_replace_updates_values(self, parser, replacer, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        updated = replacer.apply(vars_)
        assert "db.internal" in updated["DB_URL"]
        assert "db.internal" in updated["REDIS_URL"]
        assert updated["APP_NAME"] == "myapp"

    def test_replace_then_serialize_roundtrip(self, parser, replacer, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        updated = replacer.apply(vars_)
        serialized = parser.serialize(updated)
        reparsed = parser.parse(serialized)
        assert reparsed["DB_URL"] == updated["DB_URL"]
        assert reparsed["REDIS_URL"] == updated["REDIS_URL"]

    def test_no_match_preserves_all_values(self, parser, sample_env_content):
        r = EnvReplacer(pattern="NOMATCH", replacement="x")
        vars_ = parser.parse(sample_env_content)
        result = r.replace(vars_)
        assert not result.has_changes()
        assert len(result.skipped) == 0

    def test_selective_key_replace_leaves_others_intact(self, parser, sample_env_content):
        r = EnvReplacer(pattern="localhost", replacement="prod", keys=["DB_URL"])
        vars_ = parser.parse(sample_env_content)
        updated = r.apply(vars_)
        assert "prod" in updated["DB_URL"]
        assert "localhost" in updated["REDIS_URL"]
