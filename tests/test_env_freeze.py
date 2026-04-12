"""Tests for env_freeze and cli_freeze."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.env_freeze import EnvFreezer, FreezeResult, FreezeViolation
from envoy.cli_freeze import handle_freeze_command


@pytest.fixture
def freezer():
    return EnvFreezer()


@pytest.fixture
def sample_vars():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc123"}


class TestFreezeResult:
    def test_repr(self):
        r = FreezeResult(vars={"A": "1"}, violations=[], is_clean=True)
        assert "FreezeResult" in repr(r)
        assert "is_clean=True" in repr(r)

    def test_to_dict_roundtrip(self, sample_vars):
        r = FreezeResult(vars=sample_vars)
        d = r.to_dict()
        restored = FreezeResult.from_dict(d)
        assert restored.vars == sample_vars
        assert restored.frozen_at == r.frozen_at


class TestFreezeViolation:
    def test_repr(self):
        v = FreezeViolation(key="X", expected="a", actual="b")
        assert "FreezeViolation" in repr(v)
        assert "X" in repr(v)


class TestEnvFreezer:
    def test_freeze_captures_all_vars(self, freezer, sample_vars):
        result = freezer.freeze(sample_vars)
        assert result.vars == sample_vars
        assert result.is_clean is True
        assert result.violations == []

    def test_check_identical_is_clean(self, freezer, sample_vars):
        frozen = freezer.freeze(sample_vars)
        result = freezer.check(frozen, dict(sample_vars))
        assert result.is_clean is True
        assert result.violations == []

    def test_check_detects_changed_value(self, freezer, sample_vars):
        frozen = freezer.freeze(sample_vars)
        current = dict(sample_vars)
        current["DB_HOST"] = "remotehost"
        result = freezer.check(frozen, current)
        assert not result.is_clean
        assert any(v.key == "DB_HOST" for v in result.violations)

    def test_check_detects_missing_key(self, freezer, sample_vars):
        frozen = freezer.freeze(sample_vars)
        current = {k: v for k, v in sample_vars.items() if k != "SECRET"}
        result = freezer.check(frozen, current)
        assert not result.is_clean
        keys = [v.key for v in result.violations]
        assert "SECRET" in keys

    def test_check_detects_extra_key(self, freezer, sample_vars):
        frozen = freezer.freeze(sample_vars)
        current = dict(sample_vars)
        current["NEW_KEY"] = "surprise"
        result = freezer.check(frozen, current)
        assert not result.is_clean
        assert any(v.key == "NEW_KEY" for v in result.violations)


# --- CLI tests ---

class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def env_file(tmp_dir):
    p = tmp_dir / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    return p


def _out(msgs):
    def _inner(msg=""):
        msgs.append(msg)
    return _inner


class TestHandleFreezeCommand:
    def test_no_subcommand_shows_usage(self):
        args = Args(freeze_cmd=None)
        msgs = []
        rc = handle_freeze_command(args, out=_out(msgs))
        assert rc == 1
        assert any("Usage" in m for m in msgs)

    def test_snap_creates_freeze_file(self, tmp_dir, env_file):
        out_file = tmp_dir / ".envfreeze"
        args = Args(freeze_cmd="snap", file=str(env_file), output=str(out_file))
        msgs = []
        rc = handle_freeze_command(args, out=_out(msgs))
        assert rc == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert "DB_HOST" in data["vars"]

    def test_snap_missing_file_returns_error(self, tmp_dir):
        args = Args(freeze_cmd="snap", file=str(tmp_dir / "missing.env"), output=str(tmp_dir / "out"))
        msgs = []
        rc = handle_freeze_command(args, out=_out(msgs))
        assert rc == 1
        assert any("not found" in m for m in msgs)

    def test_check_clean_returns_zero(self, tmp_dir, env_file):
        out_file = tmp_dir / ".envfreeze"
        snap_args = Args(freeze_cmd="snap", file=str(env_file), output=str(out_file))
        handle_freeze_command(snap_args)
        check_args = Args(freeze_cmd="check", file=str(env_file), freeze_file=str(out_file))
        msgs = []
        rc = handle_freeze_command(check_args, out=_out(msgs))
        assert rc == 0
        assert any("OK" in m for m in msgs)

    def test_check_drift_returns_nonzero(self, tmp_dir, env_file):
        out_file = tmp_dir / ".envfreeze"
        snap_args = Args(freeze_cmd="snap", file=str(env_file), output=str(out_file))
        handle_freeze_command(snap_args)
        env_file.write_text("DB_HOST=changed\nDB_PORT=5432\n")
        check_args = Args(freeze_cmd="check", file=str(env_file), freeze_file=str(out_file))
        msgs = []
        rc = handle_freeze_command(check_args, out=_out(msgs))
        assert rc == 1
        assert any("FAIL" in m for m in msgs)
