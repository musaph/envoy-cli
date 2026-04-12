"""Tests for EnvAnnotator."""
import pytest
from envoy.env_annotate import Annotation, AnnotateResult, EnvAnnotator


@pytest.fixture
def annotator():
    return EnvAnnotator()


@pytest.fixture
def sample_vars():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "abc123"}


class TestAnnotation:
    def test_to_dict_roundtrip(self):
        ann = Annotation(key="FOO", comment="A foo var", tags=["db", "required"])
        assert Annotation.from_dict(ann.to_dict()) == ann

    def test_repr_contains_key(self):
        ann = Annotation(key="BAR", comment="bar")
        assert "BAR" in repr(ann)

    def test_from_dict_missing_tags_defaults_empty(self):
        ann = Annotation.from_dict({"key": "X", "comment": "hi"})
        assert ann.tags == []


class TestAnnotateResult:
    def test_repr(self):
        r = AnnotateResult(annotated={"A": Annotation("A", "c")}, unknown_keys=["B"])
        assert "annotated=1" in repr(r)
        assert "unknown_keys=['B']" in repr(r)


class TestEnvAnnotator:
    def test_annotate_returns_annotation(self, annotator):
        ann = annotator.annotate("DB_HOST", "Database hostname")
        assert ann.key == "DB_HOST"
        assert ann.comment == "Database hostname"

    def test_annotate_with_tags(self, annotator):
        ann = annotator.annotate("SECRET_KEY", "Secret", tags=["sensitive"])
        assert "sensitive" in ann.tags

    def test_get_returns_annotation(self, annotator):
        annotator.annotate("FOO", "foo comment")
        assert annotator.get("FOO") is not None

    def test_get_missing_returns_none(self, annotator):
        assert annotator.get("MISSING") is None

    def test_remove_existing_key(self, annotator):
        annotator.annotate("FOO", "x")
        assert annotator.remove("FOO") is True
        assert annotator.get("FOO") is None

    def test_remove_missing_key_returns_false(self, annotator):
        assert annotator.remove("NOPE") is False

    def test_apply_separates_known_and_unknown(self, annotator, sample_vars):
        annotator.annotate("DB_HOST", "host")
        annotator.annotate("GHOST_VAR", "not in file")
        result = annotator.apply(sample_vars)
        assert "DB_HOST" in result.annotated
        assert "GHOST_VAR" in result.unknown_keys

    def test_apply_empty_annotations(self, annotator, sample_vars):
        result = annotator.apply(sample_vars)
        assert result.annotated == {}
        assert result.unknown_keys == []

    def test_all_annotations_returns_copy(self, annotator):
        annotator.annotate("A", "a")
        all_ann = annotator.all_annotations()
        all_ann["B"] = Annotation("B", "b")  # mutate copy
        assert annotator.get("B") is None

    def test_overwrite_annotation(self, annotator):
        annotator.annotate("KEY", "first")
        annotator.annotate("KEY", "second")
        assert annotator.get("KEY").comment == "second"
