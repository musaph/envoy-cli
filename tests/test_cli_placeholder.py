"""Tests for handle_placeholder_command."""
import pytest
from pathlib import Path
from argparse import Namespace
from envoy.cli_placeholder import handle_placeholder_command


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("HOST=localhost\nSECRET=<YOUR_SECRET>\nEMPTY=\n")
    return f


def _args(**kwargs) -> Namespace:
    defaults = {"strict": False}
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestHandlePlaceholderCommand:
    def test_no_file_attr_shows_usage(self):
        out = []
        rc = handle_placeholder_command(Namespace(), out=out.append)
        assert rc == 1
        assert any("Usage" in line for line in out)

    def test_missing_file_returns_error(self, tmp_path):
        out = []
        rc = handle_placeholder_command(
            _args(file=str(tmp_path / "missing.env")), out=out.append
        )
        assert rc == 1
        assert any("not found" in line for line in out)

    def test_detects_placeholders(self, env_file):
        out = []
        rc = handle_placeholder_command(_args(file=str(env_file)), out=out.append)
        assert rc == 0  # non-strict, placeholders found but exit 0
        combined = "\n".join(out)
        assert "SECRET" in combined
        assert "EMPTY" in combined

    def test_strict_mode_returns_nonzero_on_placeholders(self, env_file):
        out = []
        rc = handle_placeholder_command(
            _args(file=str(env_file), strict=True), out=out.append
        )
        assert rc == 1

    def test_clean_file_returns_zero(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("HOST=localhost\nPORT=5432\n")
        out = []
        rc = handle_placeholder_command(_args(file=str(f), strict=True), out=out.append)
        assert rc == 0
        assert any("No placeholder" in line for line in out)

    def test_output_shows_checked_count(self, env_file):
        out = []
        handle_placeholder_command(_args(file=str(env_file)), out=out.append)
        assert any("Checked" in line for line in out)
