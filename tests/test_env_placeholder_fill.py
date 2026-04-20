"""Tests for EnvPlaceholderFiller."""
import pytest
from envoy.env_placeholder_fill import (
    EnvPlaceholderFiller,
    FillChange,
    FillResult,
)


@pytest.fixture
def filler():
    return EnvPlaceholderFiller()


@pytest.fixture
def strict_filler():
    return EnvPlaceholderFiller(strict=True)


@pytest.fixture
def sample_vars():
    return {
        "DB_HOST": "<DB_HOST>",
        "DB_PORT": "<DB_PORT:5432>",
        "APP_NAME": "myapp",
        "API_URL": "https://<API_HOST>/v1",
    }


# ---------------------------------------------------------------------------
# FillResult
# ---------------------------------------------------------------------------

class TestFillResult:
    def test_repr(self):
        r = FillResult(changes=[], unfilled=[], output={})
        assert "FillResult" in repr(r)
        assert "complete=True" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = FillResult()
        assert not r.has_changes

    def test_is_complete_false_when_unfilled(self):
        r = FillResult(unfilled=["DB_HOST"])
        assert not r.is_complete


# ---------------------------------------------------------------------------
# FillChange
# ---------------------------------------------------------------------------

class TestFillChange:
    def test_repr_no_default(self):
        ch = FillChange(key="K", old_value="<K>", new_value="val")
        assert "FillChange" in repr(ch)
        assert "(default)" not in repr(ch)

    def test_repr_with_default(self):
        ch = FillChange(key="K", old_value="<K:d>", new_value="d", used_default=True)
        assert "(default)" in repr(ch)


# ---------------------------------------------------------------------------
# EnvPlaceholderFiller
# ---------------------------------------------------------------------------

class TestEnvPlaceholderFiller:
    def test_fills_simple_placeholder(self, filler):
        result = filler.fill({"HOST": "<HOST>"}, {"HOST": "localhost"})
        assert result.output["HOST"] == "localhost"
        assert result.has_changes
        assert result.is_complete

    def test_uses_default_when_key_missing(self, filler):
        result = filler.fill({"PORT": "<PORT:3000>"}, {})
        assert result.output["PORT"] == "3000"
        assert result.changes[0].used_default is True
        assert result.is_complete

    def test_leaves_placeholder_when_no_context_no_default(self, filler):
        result = filler.fill({"SECRET": "<SECRET>"}, {})
        assert result.output["SECRET"] == "<SECRET>"
        assert "SECRET" in result.unfilled
        assert not result.is_complete

    def test_plain_value_unchanged(self, filler):
        result = filler.fill({"APP": "myapp"}, {})
        assert result.output["APP"] == "myapp"
        assert not result.has_changes

    def test_inline_placeholder_in_url(self, filler, sample_vars):
        ctx = {"DB_HOST": "db.example.com", "API_HOST": "api.example.com"}
        result = filler.fill(sample_vars, ctx)
        assert result.output["API_URL"] == "https://api.example.com/v1"
        assert result.output["DB_PORT"] == "5432"  # default

    def test_strict_raises_on_unfilled(self, strict_filler):
        with pytest.raises(ValueError, match="Unfilled placeholders"):
            strict_filler.fill({"X": "<X>"}, {})

    def test_strict_passes_when_all_filled(self, strict_filler):
        result = strict_filler.fill({"X": "<X>"}, {"X": "ok"})
        assert result.output["X"] == "ok"

    def test_context_overrides_default(self, filler):
        result = filler.fill({"PORT": "<PORT:3000>"}, {"PORT": "8080"})
        assert result.output["PORT"] == "8080"
        assert result.changes[0].used_default is False
