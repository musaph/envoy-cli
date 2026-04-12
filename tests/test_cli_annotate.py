"""Tests for CLI annotation subcommands."""
import pytest
from unittest.mock import patch, mock_open
from envoy.cli_annotate import handle_annotate_command


ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n"


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def _out():
    lines = []
    return lines, lines.append


class TestHandleAnnotateCommand:
    def test_no_subcommand_shows_usage(self, _out):
        lines, out = _out
        args = Args(annotate_cmd=None)
        rc = handle_annotate_command(args, output=out)
        assert rc == 1
        assert any("Usage" in l for l in lines)

    def test_missing_file_returns_error(self, _out):
        lines, out = _out
        args = Args(annotate_cmd="add", file="/no/such/file.env",
                    key="FOO", comment="c", tags=[])
        rc = handle_annotate_command(args, output=out)
        assert rc == 2
        assert any("not found" in l for l in lines)

    def test_add_annotation_for_existing_key(self, _out, tmp_path):
        lines, out = _out
        env_file = tmp_path / ".env"
        env_file.write_text(ENV_CONTENT)
        args = Args(annotate_cmd="add", file=str(env_file),
                    key="DB_HOST", comment="The DB host", tags=["db"])
        rc = handle_annotate_command(args, output=out)
        assert rc == 0
        assert any("DB_HOST" in l for l in lines)

    def test_add_annotation_warns_for_missing_key(self, _out, tmp_path):
        lines, out = _out
        env_file = tmp_path / ".env"
        env_file.write_text(ENV_CONTENT)
        args = Args(annotate_cmd="add", file=str(env_file),
                    key="GHOST", comment="not here", tags=[])
        rc = handle_annotate_command(args, output=out)
        assert rc == 0
        assert any("Warning" in l for l in lines)

    def test_show_with_no_annotations(self, _out, tmp_path):
        lines, out = _out
        env_file = tmp_path / ".env"
        env_file.write_text(ENV_CONTENT)
        args = Args(annotate_cmd="show", file=str(env_file))
        rc = handle_annotate_command(args, output=out)
        assert rc == 0
        assert any("No annotations" in l for l in lines)

    def test_unknown_subcommand_returns_error(self, _out, tmp_path):
        lines, out = _out
        env_file = tmp_path / ".env"
        env_file.write_text(ENV_CONTENT)
        args = Args(annotate_cmd="explode", file=str(env_file))
        rc = handle_annotate_command(args, output=out)
        assert rc == 1
