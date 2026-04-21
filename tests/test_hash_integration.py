"""Integration tests for EnvHasher with EnvParser and EnvExporter."""
import pytest
from envoy.parser import EnvParser
from envoy.env_hash import EnvHasher
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def hasher():
    return EnvHasher(algorithm="sha256")


@pytest.fixture
def exporter():
    return EnvExporter()


@pytest.fixture
def sample_env_content():
    return "SECRET=topsecret\nTOKEN=abc123\nAPP_NAME=envoy\n"


class TestHashWithParser:
    def test_parse_then_hash_all_values(self, parser, hasher, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        result = hasher.hash_vars(vars_)
        assert result.has_changes()
        assert set(result.changed_keys()) == {"SECRET", "TOKEN", "APP_NAME"}

    def test_apply_then_export_produces_valid_env(self, parser, hasher, exporter, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        hashed = hasher.apply(vars_)
        exported = exporter.export(hashed, fmt="dotenv")
        assert exported.content
        assert "APP_NAME=" in exported.content
        # values should no longer be the originals
        assert "topsecret" not in exported.content
        assert "abc123" not in exported.content

    def test_selective_hash_preserves_plain_values(self, parser, exporter, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        selective = EnvHasher(algorithm="sha256", keys=["SECRET"])
        hashed = selective.apply(vars_)
        exported = exporter.export(hashed, fmt="dotenv")
        assert "abc123" in exported.content   # TOKEN untouched
        assert "envoy" in exported.content    # APP_NAME untouched
        assert "topsecret" not in exported.content  # SECRET hashed

    def test_hash_idempotent_same_input(self, parser, hasher, sample_env_content):
        vars_ = parser.parse(sample_env_content)
        first = hasher.apply(vars_)
        second = hasher.apply(vars_)
        assert first == second
