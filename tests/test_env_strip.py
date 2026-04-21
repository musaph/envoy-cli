"""Tests for EnvStripper."""
import pytest
from envoy.env_strip import EnvStripper, StripChange, StripResult


@pytest.fixture
def prefix_stripper():
    return EnvStripper(prefix="dev_")


@pytest.fixture
def suffix_stripper():
    return EnvStripper(suffix="_value")


@pytest.fixture
def both_stripper():
    return EnvStripper(prefix="pre_", suffix="_suf")


@pytest.fixture
def sample_vars():
    return {
        "dev_HOST": "dev_localhost",
        "dev_PORT": "dev_8080",
        "APP_NAME": "myapp",
    }


class TestStripResult:
    def test_repr(self):
        r = StripResult(changes=[StripChange("K", "old", "new")], unchanged=["X"])
        assert "StripResult" in repr(r)
        assert "changes=1" in repr(r)
        assert "unchanged=1" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = StripResult()
        assert r.has_changes() is False

    def test_has_changes_true_when_populated(self):
        r = StripResult(changes=[StripChange("K", "a", "b")])
        assert r.has_changes() is True

    def test_changed_keys(self):
        r = StripResult(changes=[StripChange("A", "x", "y"), StripChange("B", "p", "q")])
        assert r.changed_keys() == ["A", "B"]


class TestEnvStripper:
    def test_strip_prefix(self, prefix_stripper):
        result = prefix_stripper.strip({"dev_HOST": "dev_localhost", "PORT": "8080"})
        keys = result.changed_keys()
        assert "dev_HOST" in keys
        assert "PORT" not in keys

    def test_strip_prefix_value(self, prefix_stripper):
        out = prefix_stripper.apply({"dev_HOST": "dev_localhost"})
        assert out["dev_HOST"] == "dev_localhost"  # key not changed, only value

    def test_strip_suffix(self, suffix_stripper):
        result = suffix_stripper.strip({"KEY": "hello_value", "OTHER": "world"})
        assert "KEY" in result.changed_keys()
        assert "OTHER" in result.unchanged

    def test_strip_suffix_value(self, suffix_stripper):
        out = suffix_stripper.apply({"KEY": "hello_value"})
        assert out["KEY"] == "hello"

    def test_strip_both(self, both_stripper):
        out = both_stripper.apply({"X": "pre_hello_suf"})
        assert out["X"] == "hello"

    def test_no_match_leaves_unchanged(self, prefix_stripper):
        out = prefix_stripper.apply({"HOST": "localhost"})
        assert out["HOST"] == "localhost"

    def test_selective_keys(self):
        stripper = EnvStripper(prefix="dev_", keys=["dev_HOST"])
        out = stripper.apply({"dev_HOST": "dev_localhost", "dev_PORT": "dev_8080"})
        assert out["dev_HOST"] == "dev_localhost"
        assert out["dev_PORT"] == "dev_8080"  # not in keys list, untouched

    def test_apply_preserves_all_keys(self, prefix_stripper, sample_vars):
        out = prefix_stripper.apply(sample_vars)
        assert set(out.keys()) == set(sample_vars.keys())

    def test_unchanged_listed_correctly(self, prefix_stripper):
        result = prefix_stripper.strip({"dev_X": "dev_val", "NORMAL": "val"})
        assert "NORMAL" in result.unchanged
        assert "dev_X" not in result.unchanged

    def test_empty_prefix_no_change(self):
        stripper = EnvStripper(prefix="")
        out = stripper.apply({"KEY": "value"})
        assert out["KEY"] == "value"
