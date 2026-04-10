"""Tests for envoy.env_tag — EnvTagger and TagResult."""
import pytest
from envoy.env_tag import EnvTagger, TagResult


@pytest.fixture
def tagger() -> EnvTagger:
    return EnvTagger(
        rules={
            "secret": ["SECRET_", "PASSWORD", "TOKEN"],
            "database": ["DB_", "DATABASE_"],
            "feature": ["FEATURE_FLAG_"],
        }
    )


@pytest.fixture
def sample_vars() -> dict:
    return {
        "SECRET_KEY": "abc",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "FEATURE_FLAG_DARK_MODE": "true",
        "APP_NAME": "envoy",
        "DEBUG": "false",
    }


# --- TagResult ---

class TestTagResult:
    def test_repr(self):
        r = TagResult(tagged={"K": ["t"]}, untagged=["X"], warnings=["w"])
        assert "tagged=1" in repr(r)
        assert "untagged=1" in repr(r)
        assert "warnings=1" in repr(r)

    def test_defaults_are_empty(self):
        r = TagResult()
        assert r.tagged == {}
        assert r.untagged == []
        assert r.warnings == []


# --- EnvTagger ---

class TestEnvTagger:
    def test_tag_returns_tag_result(self, tagger, sample_vars):
        result = tagger.tag(sample_vars)
        assert isinstance(result, TagResult)

    def test_secret_key_tagged(self, tagger, sample_vars):
        result = tagger.tag(sample_vars)
        assert "SECRET_KEY" in result.tagged
        assert "secret" in result.tagged["SECRET_KEY"]

    def test_db_keys_tagged_as_database(self, tagger, sample_vars):
        result = tagger.tag(sample_vars)
        assert "DB_HOST" in result.tagged
        assert "database" in result.tagged["DB_HOST"]
        assert "DB_PORT" in result.tagged

    def test_untagged_keys_collected(self, tagger, sample_vars):
        result = tagger.tag(sample_vars)
        assert "APP_NAME" in result.untagged
        assert "DEBUG" in result.untagged

    def test_keys_with_tag_database(self, tagger, sample_vars):
        db_keys = tagger.keys_with_tag(sample_vars, "database")
        assert set(db_keys) == {"DB_HOST", "DB_PORT"}

    def test_keys_with_unknown_tag_returns_empty(self, tagger, sample_vars):
        assert tagger.keys_with_tag(sample_vars, "nonexistent") == []

    def test_all_tags_returns_configured_names(self, tagger):
        assert tagger.all_tags() == {"secret", "database", "feature"}

    def test_add_rule_extends_tag(self, tagger):
        tagger.add_rule("secret", "API_")
        vars = {"API_KEY": "xyz"}
        result = tagger.tag(vars)
        assert "API_KEY" in result.tagged
        assert "secret" in result.tagged["API_KEY"]

    def test_empty_rules_tags_nothing(self, sample_vars):
        t = EnvTagger()
        result = t.tag(sample_vars)
        assert result.tagged == {}
        assert set(result.untagged) == set(sample_vars.keys())

    def test_feature_flag_tagged(self, tagger, sample_vars):
        result = tagger.tag(sample_vars)
        assert "FEATURE_FLAG_DARK_MODE" in result.tagged
        assert "feature" in result.tagged["FEATURE_FLAG_DARK_MODE"]
