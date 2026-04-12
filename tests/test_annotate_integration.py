"""Integration tests: EnvAnnotator + EnvParser."""
import pytest
from envoy.env_annotate import EnvAnnotator
from envoy.parser import EnvParser


RAW_ENV = """
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=supersecret
DEBUG=true
""".strip()


@pytest.fixture
def parser():
    return EnvParser()


@pytest.fixture
def annotator():
    return EnvAnnotator()


class TestAnnotatorWithParser:
    def test_parse_then_annotate_known_keys(self, parser, annotator):
        vars_ = parser.parse(RAW_ENV)
        annotator.annotate("DB_HOST", "Hostname for the database", tags=["db"])
        annotator.annotate("SECRET_KEY", "App secret", tags=["sensitive"])
        result = annotator.apply(vars_)
        assert "DB_HOST" in result.annotated
        assert "SECRET_KEY" in result.annotated
        assert result.unknown_keys == []

    def test_unknown_annotation_reported(self, parser, annotator):
        vars_ = parser.parse(RAW_ENV)
        annotator.annotate("NONEXISTENT", "ghost")
        result = annotator.apply(vars_)
        assert "NONEXISTENT" in result.unknown_keys
        assert "NONEXISTENT" not in result.annotated

    def test_tags_preserved_through_roundtrip(self, parser, annotator):
        vars_ = parser.parse(RAW_ENV)
        annotator.annotate("DEBUG", "Debug flag", tags=["optional", "bool"])
        result = annotator.apply(vars_)
        ann = result.annotated["DEBUG"]
        assert "optional" in ann.tags
        assert "bool" in ann.tags

    def test_all_vars_can_be_annotated(self, parser, annotator):
        vars_ = parser.parse(RAW_ENV)
        for key in vars_:
            annotator.annotate(key, f"Description of {key}")
        result = annotator.apply(vars_)
        assert len(result.annotated) == len(vars_)
        assert result.unknown_keys == []
