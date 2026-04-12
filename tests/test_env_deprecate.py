"""Tests for env_deprecate and cli_deprecate."""
import os
import pytest

from envoy.env_deprecate import (
    DeprecationEntry,
    DeprecationResult,
    EnvDeprecationChecker,
)
from envoy.cli_deprecate import handle_deprecate_command, _parse_rule


@pytest.fixture
def checker():
    return EnvDeprecationChecker([
        DeprecationEntry("OLD_API_KEY", "Use NEW_API_KEY", "NEW_API_KEY"),
        DeprecationEntry("LEGACY_HOST", "Host config moved"),
    ])


# --- DeprecationEntry ---

def test_to_dict_roundtrip():
    e = DeprecationEntry("FOO", "reason", "BAR")
    assert DeprecationEntry.from_dict(e.to_dict()) == e


def test_repr_contains_key():
    e = DeprecationEntry("FOO", "old", "BAR")
    assert "FOO" in repr(e)
    assert "BAR" in repr(e)


def test_repr_no_replacement():
    e = DeprecationEntry("FOO", "old")
    assert "->" not in repr(e)


# --- DeprecationResult ---

def test_has_violations_false_when_empty():
    r = DeprecationResult()
    assert not r.has_violations


def test_has_violations_true_when_keys_present():
    r = DeprecationResult(present_keys=["OLD_API_KEY"])
    assert r.has_violations


def test_repr_contains_counts():
    r = DeprecationResult(present_keys=["X"], deprecated=[DeprecationEntry("X", "r")])
    assert "1" in repr(r)


# --- EnvDeprecationChecker ---

def test_check_no_violations(checker):
    result = checker.check({"NEW_API_KEY": "abc", "HOST": "localhost"})
    assert not result.has_violations


def test_check_finds_deprecated_key(checker):
    result = checker.check({"OLD_API_KEY": "secret", "PORT": "8080"})
    assert result.has_violations
    assert "OLD_API_KEY" in result.present_keys


def test_check_multiple_violations(checker):
    result = checker.check({"OLD_API_KEY": "x", "LEGACY_HOST": "y"})
    assert len(result.present_keys) == 2


def test_suggestions_returns_replacement(checker):
    s = checker.suggestions({"OLD_API_KEY": "val"})
    assert s["OLD_API_KEY"] == "NEW_API_KEY"


def test_suggestions_none_when_no_replacement(checker):
    s = checker.suggestions({"LEGACY_HOST": "val"})
    assert s["LEGACY_HOST"] is None


def test_register_adds_entry():
    c = EnvDeprecationChecker()
    c.register("GONE", "removed", "NEW")
    result = c.check({"GONE": "1"})
    assert result.has_violations


# --- _parse_rule ---

def test_parse_rule_with_replacement():
    e = _parse_rule("OLD:deprecated:NEW")
    assert e.key == "OLD"
    assert e.replacement == "NEW"


def test_parse_rule_without_replacement():
    e = _parse_rule("OLD:no longer used")
    assert e.replacement is None


def test_parse_rule_invalid_returns_none():
    assert _parse_rule("NOCODON") is None


# --- CLI ---

class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_no_subcommand_shows_usage():
    out = []
    rc = handle_deprecate_command(_Args(), out.append)
    assert rc == 1
    assert "Usage" in out[0]


def test_missing_file_returns_error(tmp_path):
    out = []
    args = _Args(deprecate_cmd="check", file=str(tmp_path / "missing.env"), rules=[])
    rc = handle_deprecate_command(args, out.append)
    assert rc == 2


def test_check_clean_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("NEW_API_KEY=abc\nHOST=localhost\n")
    args = _Args(deprecate_cmd="check", file=str(f), rules=["OLD_API_KEY:use NEW_API_KEY:NEW_API_KEY"])
    out = []
    rc = handle_deprecate_command(args, out.append)
    assert rc == 0


def test_check_with_violation(tmp_path):
    f = tmp_path / ".env"
    f.write_text("OLD_API_KEY=secret\n")
    args = _Args(deprecate_cmd="check", file=str(f), rules=["OLD_API_KEY:use NEW_API_KEY:NEW_API_KEY"])
    out = []
    rc = handle_deprecate_command(args, out.append)
    assert rc == 3
    combined = "\n".join(out)
    assert "OLD_API_KEY" in combined
    assert "NEW_API_KEY" in combined
