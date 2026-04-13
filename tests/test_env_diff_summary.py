"""Tests for EnvDiffSummarizer and CLI handler."""
import argparse
import json
from pathlib import Path

import pytest

from envoy.env_diff_summary import DiffSummaryEntry, DiffSummaryResult, EnvDiffSummarizer
from envoy.cli_diff_summary import handle_diff_summary_command


@pytest.fixture
def summarizer():
    return EnvDiffSummarizer()


@pytest.fixture
def old_vars():
    return {"APP_NAME": "myapp", "DEBUG": "true", "PORT": "8080"}


@pytest.fixture
def new_vars():
    return {"APP_NAME": "myapp", "DEBUG": "false", "LOG_LEVEL": "info"}


class TestDiffSummaryResult:
    def test_repr(self):
        r = DiffSummaryResult()
        assert "DiffSummaryResult" in repr(r)

    def test_has_differences_false_when_empty(self):
        assert DiffSummaryResult().has_differences is False

    def test_has_differences_true_when_added(self):
        e = DiffSummaryEntry(key="X", status="added", new_value="1")
        assert DiffSummaryResult(entries=[e]).has_differences is True


class TestEnvDiffSummarizer:
    def test_identical_vars_all_unchanged(self, summarizer, old_vars):
        result = summarizer.summarise(old_vars, old_vars)
        assert not result.has_differences
        assert len(result.unchanged) == len(old_vars)

    def test_detects_added_key(self, summarizer, old_vars, new_vars):
        result = summarizer.summarise(old_vars, new_vars)
        added_keys = [e.key for e in result.added]
        assert "LOG_LEVEL" in added_keys

    def test_detects_removed_key(self, summarizer, old_vars, new_vars):
        result = summarizer.summarise(old_vars, new_vars)
        removed_keys = [e.key for e in result.removed]
        assert "PORT" in removed_keys

    def test_detects_changed_key(self, summarizer, old_vars, new_vars):
        result = summarizer.summarise(old_vars, new_vars)
        changed_keys = [e.key for e in result.changed]
        assert "DEBUG" in changed_keys

    def test_unchanged_key_present(self, summarizer, old_vars, new_vars):
        result = summarizer.summarise(old_vars, new_vars)
        unchanged_keys = [e.key for e in result.unchanged]
        assert "APP_NAME" in unchanged_keys

    def test_ignore_case_treats_as_equal(self):
        s = EnvDiffSummarizer(ignore_case=True)
        result = s.summarise({"K": "Hello"}, {"K": "hello"})
        assert not result.has_differences
        assert len(result.unchanged) == 1

    def test_case_sensitive_detects_change(self, summarizer):
        result = summarizer.summarise({"K": "Hello"}, {"K": "hello"})
        assert len(result.changed) == 1

    def test_empty_old_all_added(self, summarizer):
        result = summarizer.summarise({}, {"A": "1", "B": "2"})
        assert len(result.added) == 2
        assert not result.removed

    def test_empty_new_all_removed(self, summarizer):
        result = summarizer.summarise({"A": "1", "B": "2"}, {})
        assert len(result.removed) == 2


class TestHandleDiffSummaryCommand:
    def _args(self, old_file, new_file, fmt="text", ignore_case=False, only_changes=False):
        a = argparse.Namespace()
        a.old_file = str(old_file)
        a.new_file = str(new_file)
        a.format = fmt
        a.ignore_case = ignore_case
        a.only_changes = only_changes
        return a

    def test_missing_old_file_returns_error(self, tmp_path):
        new_f = tmp_path / "new.env"
        new_f.write_text("A=1")
        out = []
        code = handle_diff_summary_command(
            self._args(tmp_path / "ghost.env", new_f), out=out.append
        )
        assert code == 1
        assert any("not found" in line for line in out)

    def test_missing_new_file_returns_error(self, tmp_path):
        old_f = tmp_path / "old.env"
        old_f.write_text("A=1")
        out = []
        code = handle_diff_summary_command(
            self._args(old_f, tmp_path / "ghost.env"), out=out.append
        )
        assert code == 1

    def test_text_output_shows_summary_line(self, tmp_path):
        old_f = tmp_path / "old.env"
        new_f = tmp_path / "new.env"
        old_f.write_text("A=1\nB=2")
        new_f.write_text("A=1\nC=3")
        out = []
        code = handle_diff_summary_command(self._args(old_f, new_f), out=out.append)
        assert code == 0
        combined = "\n".join(out)
        assert "Summary:" in combined

    def test_json_output_is_parseable(self, tmp_path):
        old_f = tmp_path / "old.env"
        new_f = tmp_path / "new.env"
        old_f.write_text("A=1")
        new_f.write_text("A=2")
        out = []
        code = handle_diff_summary_command(self._args(old_f, new_f, fmt="json"), out=out.append)
        assert code == 0
        data = json.loads("\n".join(out))
        assert isinstance(data, list)
        assert data[0]["key"] == "A"

    def test_no_subcommand_shows_usage(self):
        out = []
        code = handle_diff_summary_command(argparse.Namespace(), out=out.append)
        assert code == 1
        assert "Usage" in out[0]
