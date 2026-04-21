import os
import pytest
from envoy.cli_encode import handle_encode_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("URL_VAR=hello world\nSAFE_VAR=okay\n")
    return str(f)


@pytest.fixture
def _out():
    lines = []
    return lines, lambda msg: lines.append(msg)


def test_no_subcommand_shows_usage(_out):
    lines, out = _out
    args = Args(encode_cmd=None)
    rc = handle_encode_command(args, out)
    assert rc == 1
    assert any("Usage" in l for l in lines)


def test_unknown_subcommand_returns_error(_out):
    lines, out = _out
    args = Args(encode_cmd="bogus")
    rc = handle_encode_command(args, out)
    assert rc == 1


def test_missing_file_returns_error(tmp_path, _out):
    lines, out = _out
    args = Args(
        encode_cmd="run",
        file=str(tmp_path / "missing.env"),
        encoding="url",
        keys=None,
        dry_run=False,
    )
    rc = handle_encode_command(args, out)
    assert rc == 1
    assert any("not found" in l for l in lines)


def test_dry_run_does_not_modify_file(env_file, _out):
    lines, out = _out
    original = open(env_file).read()
    args = Args(
        encode_cmd="run",
        file=env_file,
        encoding="url",
        keys=None,
        dry_run=True,
    )
    rc = handle_encode_command(args, out)
    assert rc == 0
    assert open(env_file).read() == original
    assert any("Dry run" in l for l in lines)


def test_run_encodes_and_writes_file(env_file, _out):
    lines, out = _out
    args = Args(
        encode_cmd="run",
        file=env_file,
        encoding="url",
        keys=None,
        dry_run=False,
    )
    rc = handle_encode_command(args, out)
    assert rc == 0
    content = open(env_file).read()
    assert "hello%20world" in content


def test_no_changes_reports_clean(tmp_path, _out):
    lines, out = _out
    f = tmp_path / ".env"
    f.write_text("KEY=safe\n")
    args = Args(
        encode_cmd="run",
        file=str(f),
        encoding="url",
        keys=None,
        dry_run=False,
    )
    rc = handle_encode_command(args, out)
    assert rc == 0
    assert any("No values" in l for l in lines)
