"""Tests for envoy.cli_compress module."""

import pytest
from pathlib import Path
from envoy.cli_compress import handle_compress_command
from envoy.compress import EnvCompressor


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def tmp_env(tmp_path) -> Path:
    f = tmp_path / ".env"
    f.write_text("DB_HOST=localhost\nPORT=5432\n")
    return f


class TestHandleCompressCommand:
    def test_no_subcommand_shows_usage(self):
        args = Args(compress_cmd=None)
        out_lines = []
        rc = handle_compress_command(args, out=out_lines.append)
        assert rc == 1
        assert any("Usage" in l for l in out_lines)

    def test_pack_creates_output_file(self, tmp_env, tmp_path):
        out_path = tmp_path / "packed.env.zz"
        args = Args(compress_cmd="pack", file=str(tmp_env), output=str(out_path), level=6)
        rc = handle_compress_command(args, out=print)
        assert rc == 0
        assert out_path.exists()
        assert out_path.stat().st_size > 0

    def test_pack_missing_file_reports_error(self, tmp_path):
        args = Args(compress_cmd="pack", file=str(tmp_path / "ghost.env"), output=None, level=6)
        out_lines = []
        rc = handle_compress_command(args, out=out_lines.append)
        assert rc == 1
        assert any("not found" in l for l in out_lines)

    def test_unpack_roundtrip(self, tmp_env, tmp_path):
        packed = tmp_path / "packed.env.zz"
        pack_args = Args(compress_cmd="pack", file=str(tmp_env), output=str(packed), level=6)
        handle_compress_command(pack_args)

        restored = tmp_path / "restored.env"
        unpack_args = Args(compress_cmd="unpack", file=str(packed), output=str(restored), level=6)
        rc = handle_compress_command(unpack_args, out=print)
        assert rc == 0
        assert restored.read_text() == tmp_env.read_text()

    def test_unpack_missing_file_reports_error(self, tmp_path):
        args = Args(compress_cmd="unpack", file=str(tmp_path / "nope.zz"), output=None, level=6)
        out_lines = []
        rc = handle_compress_command(args, out=out_lines.append)
        assert rc == 1
        assert any("not found" in l for l in out_lines)

    def test_stats_shows_compress_result(self, tmp_env):
        args = Args(compress_cmd="stats", file=str(tmp_env), level=6)
        out_lines = []
        rc = handle_compress_command(args, out=out_lines.append)
        assert rc == 0
        assert any("CompressResult" in l for l in out_lines)

    def test_stats_missing_file_reports_error(self, tmp_path):
        args = Args(compress_cmd="stats", file=str(tmp_path / "missing.env"), level=6)
        out_lines = []
        rc = handle_compress_command(args, out=out_lines.append)
        assert rc == 1

    def test_unknown_subcommand_returns_error(self):
        args = Args(compress_cmd="explode", level=6)
        out_lines = []
        rc = handle_compress_command(args, out=out_lines.append)
        assert rc == 1
        assert any("Unknown" in l for l in out_lines)
