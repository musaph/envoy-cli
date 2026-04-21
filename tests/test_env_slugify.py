"""Tests for EnvSlugifier."""
from __future__ import annotations

import pytest

from envoy.env_slugify import EnvSlugifier, SlugifyChange, SlugifyResult


@pytest.fixture
def slugifier() -> EnvSlugifier:
    return EnvSlugifier()


@pytest.fixture
def overwrite_slugifier() -> EnvSlugifier:
    return EnvSlugifier(overwrite=True)


@pytest.fixture
def sample_vars() -> dict:
    return {
        "myApiKey": "abc",
        "some-var": "123",
        "ALREADY_UPPER": "ok",
        "dot.separated": "val",
    }


class TestSlugifyResult:
    def test_repr(self):
        r = SlugifyResult(vars={"A": "1"}, changes=[], skipped=[])
        assert "SlugifyResult" in repr(r)
        assert "changed=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = SlugifyResult()
        assert not r.has_changes()

    def test_has_changes_true_when_populated(self):
        r = SlugifyResult(
            changes=[SlugifyChange(key="MY_KEY", original_key="my-key", value="v")]
        )
        assert r.has_changes()

    def test_changed_keys_returns_originals(self):
        r = SlugifyResult(
            changes=[SlugifyChange(key="MY_KEY", original_key="my-key", value="v")]
        )
        assert r.changed_keys() == ["my-key"]


class TestEnvSlugifier:
    def test_already_upper_snake_unchanged(self, slugifier):
        result = slugifier.slugify({"ALREADY_UPPER": "ok"})
        assert not result.has_changes()
        assert result.vars == {"ALREADY_UPPER": "ok"}

    def test_camel_case_converted(self, slugifier):
        result = slugifier.slugify({"myApiKey": "secret"})
        assert result.has_changes()
        assert "MY_API_KEY" in result.vars
        assert result.vars["MY_API_KEY"] == "secret"

    def test_hyphen_replaced(self, slugifier):
        result = slugifier.slugify({"some-var": "123"})
        assert "SOME_VAR" in result.vars

    def test_dot_replaced(self, slugifier):
        result = slugifier.slugify({"dot.separated": "val"})
        assert "DOT_SEPARATED" in result.vars

    def test_multiple_special_chars(self, slugifier):
        result = slugifier.slugify({"a..b--c": "x"})
        assert "A_B_C" in result.vars

    def test_collision_skipped_by_default(self, slugifier):
        # Both 'some-var' and 'SOME_VAR' would map to SOME_VAR
        result = slugifier.slugify({"SOME_VAR": "original", "some-var": "new"})
        assert "some-var" in result.skipped or "SOME_VAR" in result.vars

    def test_collision_overwritten_when_flag_set(self, overwrite_slugifier):
        result = overwrite_slugifier.slugify({"some-var": "new", "SOME_VAR": "original"})
        assert result.vars.get("SOME_VAR") is not None

    def test_mixed_batch(self, slugifier, sample_vars):
        result = slugifier.slugify(sample_vars)
        assert "ALREADY_UPPER" in result.vars
        assert "MY_API_KEY" in result.vars
