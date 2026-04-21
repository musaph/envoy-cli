import pytest
from envoy.cli_mask_keys import handle_mask_keys_command


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_TOKEN=secret\nDATABASE_URL=postgres://localhost\nPORT=8080\n")
    return str(p)


@pytest.fixture
def _out():
    lines = []
    return lines, lines.append


def test_no_subcommand_shows_usage(_out):
    lines, out = _out
    args = Args(mask_keys_cmd=None)
    rc = handle_mask_keys_command(args, out=out)
    assert rc == 1
    assert any("Usage" in line for line in lines)


def test_unknown_subcommand_returns_error(_out):
    lines, out = _out
    args = Args(mask_keys_cmd="nonexistent")
    rc = handle_mask_keys_command(args, out=out)
    assert rc == 1
    assert any("Unknown" in line for line in lines)


def test_missing_file_returns_error(_out):
    lines, out = _out
    args = Args(mask_keys_cmd="run", file="/nonexistent/.env", visible=2, char="*", keys=None)
    rc = handle_mask_keys_command(args, out=out)
    assert rc == 1
    assert any("not found" in line for line in lines)


def test_run_masks_all_keys(env_file, _out):
    lines, out = _out
    args = Args(mask_keys_cmd="run", file=env_file, visible=2, char="*", keys=None)
    rc = handle_mask_keys_command(args, out=out)
    assert rc == 0
    combined = "\n".join(lines)
    assert "Masked" in combined


def test_run_selective_keys(env_file, _out):
    lines, out = _out
    args = Args(mask_keys_cmd="run", file=env_file, visible=2, char="*", keys=["API_TOKEN"])
    rc = handle_mask_keys_command(args, out=out)
    assert rc == 0
    combined = "\n".join(lines)
    assert "API_TOKEN" in combined


def test_run_no_changes_when_short_keys(_out, tmp_path):
    lines, out = _out
    p = tmp_path / ".env"
    p.write_text("AB=1\nCD=2\n")
    args = Args(mask_keys_cmd="run", file=str(p), visible=10, char="*", keys=None)
    rc = handle_mask_keys_command(args, out=out)
    assert rc == 0
    assert any("No keys" in line for line in lines)


def test_run_custom_mask_char(env_file, _out):
    lines, out = _out
    args = Args(mask_keys_cmd="run", file=env_file, visible=1, char="#", keys=["DATABASE_URL"])
    rc = handle_mask_keys_command(args, out=out)
    assert rc == 0
    combined = "\n".join(lines)
    assert "#" in combined
