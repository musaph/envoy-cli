"""Tests for envoy.hooks and envoy.cli_hooks."""
from __future__ import annotations

import argparse
import sys
from unittest.mock import MagicMock, patch

import pytest

from envoy.hooks import HookEvent, HookResult, HookRunner
from envoy.cli_hooks import handle_hooks_command


# ---------------------------------------------------------------------------
# HookRunner unit tests
# ---------------------------------------------------------------------------

class TestHookRunner:
    def test_from_config_single_string(self):
        runner = HookRunner.from_config({"pre-push": "echo hello"})
        assert runner.hooks[HookEvent.PRE_PUSH] == ["echo hello"]

    def test_from_config_list(self):
        runner = HookRunner.from_config({"post-pull": ["echo a", "echo b"]})
        assert runner.hooks[HookEvent.POST_PULL] == ["echo a", "echo b"]

    def test_from_config_ignores_unknown_events(self):
        runner = HookRunner.from_config({"bogus-event": "echo x"})
        assert runner.hooks == {}

    def test_has_hooks_true(self):
        runner = HookRunner.from_config({"pre-push": "echo hi"})
        assert runner.has_hooks(HookEvent.PRE_PUSH) is True

    def test_has_hooks_false(self):
        runner = HookRunner()
        assert runner.has_hooks(HookEvent.PRE_PUSH) is False

    def test_run_successful_command(self):
        runner = HookRunner.from_config({"pre-push": "echo envoy"})
        results = runner.run(HookEvent.PRE_PUSH)
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].stdout == "envoy"

    def test_run_failing_command(self):
        runner = HookRunner.from_config({"pre-push": "exit 42"})
        results = runner.run(HookEvent.PRE_PUSH)
        assert results[0].returncode == 42
        assert results[0].success is False

    def test_run_no_hooks_returns_empty(self):
        runner = HookRunner()
        results = runner.run(HookEvent.PRE_PUSH)
        assert results == []

    def test_run_timeout(self):
        runner = HookRunner.from_config({"pre-push": "sleep 60"})
        results = runner.run(HookEvent.PRE_PUSH, timeout=1)
        assert results[0].returncode == 124
        assert "timed out" in results[0].stderr


# ---------------------------------------------------------------------------
# CLI handler tests
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"hooks_cmd": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_config(hooks: dict | None = None) -> MagicMock:
    cfg = MagicMock()
    cfg.get.return_value = hooks or {}
    return cfg


class TestHandleHooksCommand:
    def test_no_subcommand_shows_usage(self):
        out_lines: list[str] = []
        code = handle_hooks_command(_make_args(), _make_config(), out=out_lines.append)
        assert code == 1
        assert any("Usage" in l for l in out_lines)

    def test_list_empty(self):
        out_lines: list[str] = []
        code = handle_hooks_command(_make_args(hooks_cmd="list"), _make_config(), out=out_lines.append)
        assert code == 0
        assert any("No hooks" in l for l in out_lines)

    def test_list_with_hooks(self):
        out_lines: list[str] = []
        cfg = _make_config({"pre-push": ["echo a"]})
        code = handle_hooks_command(_make_args(hooks_cmd="list"), cfg, out=out_lines.append)
        assert code == 0
        assert any("pre-push" in l for l in out_lines)

    def test_add_hook(self):
        out_lines: list[str] = []
        cfg = _make_config({})
        args = _make_args(hooks_cmd="add", event="pre-push", command="echo added")
        code = handle_hooks_command(args, cfg, out=out_lines.append)
        assert code == 0
        cfg.set.assert_called_once()
        assert any("added" in l for l in out_lines)

    def test_remove_existing_hook(self):
        out_lines: list[str] = []
        cfg = _make_config({"pre-push": ["echo hi"]})
        args = _make_args(hooks_cmd="remove", event="pre-push", command="echo hi")
        code = handle_hooks_command(args, cfg, out=out_lines.append)
        assert code == 0
        cfg.set.assert_called_once()

    def test_remove_missing_hook_returns_error(self):
        out_lines: list[str] = []
        cfg = _make_config({"pre-push": ["echo hi"]})
        args = _make_args(hooks_cmd="remove", event="pre-push", command="echo missing")
        code = handle_hooks_command(args, cfg, out=out_lines.append)
        assert code == 1

    def test_run_no_hooks_registered(self):
        out_lines: list[str] = []
        cfg = _make_config({})
        args = _make_args(hooks_cmd="run", event="post-push")
        code = handle_hooks_command(args, cfg, out=out_lines.append)
        assert code == 0
        assert any("No hooks" in l for l in out_lines)
