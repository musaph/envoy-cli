"""Tests for envoy.cli_resolve."""
import os
import pytest
from envoy.cli_resolve import handle_resolve_command


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("BASE=http\nURL=${BASE}://example.com\nPORT=8080\n")
    return str(p)


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _args(**kwargs):
    defaults = {"resolve_cmd": "run", "strict": False}
    defaults.update(kwargs)
    return Args(**defaults)


class TestHandleResolveCommand:
    def test_no_subcommand_shows_usage(self):
        out = []
        args = Args(resolve_cmd=None)
        rc = handle_resolve_command(args, print_fn=out.append)
        assert rc == 1
        assert any("Usage" in line for line in out)

    def test_unknown_subcommand_returns_error(self):
        out = []
        args = Args(resolve_cmd="bogus")
        rc = handle_resolve_command(args, print_fn=out.append)
        assert rc == 1

    def test_missing_file_returns_error(self, tmp_path):
        out = []
        args = _args(file=str(tmp_path / "nope.env"))
        rc = handle_resolve_command(args, print_fn=out.append)
        assert rc == 1
        assert any("not found" in line for line in out)

    def test_run_prints_resolved_vars(self, env_file):
        out = []
        args = _args(file=env_file)
        rc = handle_resolve_command(args, print_fn=out.append)
        assert rc == 0
        joined = "\n".join(out)
        assert "URL=http://example.com" in joined
        assert "PORT=8080" in joined

    def test_run_warns_on_unresolved(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("URL=${MISSING}/path\n")
        out = []
        args = _args(file=str(f), strict=False)
        rc = handle_resolve_command(args, print_fn=out.append)
        assert rc == 0
        assert any("Warning" in line for line in out)

    def test_strict_mode_fails_on_unresolved(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("URL=${MISSING}/path\n")
        out = []
        args = _args(file=str(f), strict=True)
        rc = handle_resolve_command(args, print_fn=out.append)
        assert rc == 1

    def test_no_expansion_needed_exits_cleanly(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("FOO=bar\nBAZ=qux\n")
        out = []
        args = _args(file=str(f))
        rc = handle_resolve_command(args, print_fn=out.append)
        assert rc == 0
        assert any("FOO=bar" in line for line in out)
