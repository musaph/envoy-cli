import pytest
from envoy.cli_whitelist import handle_whitelist_command


class Args:
    def __init__(self, file, allowed_keys, strict=True, filter_only=False):
        self.file = file
        self.allowed_keys = allowed_keys
        self.strict = strict
        self.filter_only = filter_only


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nPORT=8080\nSECRET_KEY=abc123\n")
    return str(p)


@pytest.fixture
def _out():
    lines = []
    return lines, lines.append


def test_no_file_attr_shows_usage(_out):
    lines, out = _out

    class NoFile:
        pass

    rc = handle_whitelist_command(NoFile(), out)
    assert rc == 1
    assert any("Usage" in l for l in lines)


def test_missing_file_returns_error(tmp_path, _out):
    lines, out = _out
    args = Args(file=str(tmp_path / "missing.env"), allowed_keys=["APP_NAME"])
    rc = handle_whitelist_command(args, out)
    assert rc == 1
    assert any("not found" in l for l in lines)


def test_all_keys_allowed_returns_zero(env_file, _out):
    lines, out = _out
    args = Args(file=env_file, allowed_keys=["APP_NAME", "PORT", "SECRET_KEY"])
    rc = handle_whitelist_command(args, out)
    assert rc == 0
    assert any("Violations: 0" in l for l in lines)


def test_violation_reported_for_unlisted_key(env_file, _out):
    lines, out = _out
    args = Args(file=env_file, allowed_keys=["APP_NAME", "PORT"])
    rc = handle_whitelist_command(args, out)
    assert rc == 1
    assert any("VIOLATION" in l for l in lines)


def test_filter_mode_outputs_only_allowed(env_file, _out):
    lines, out = _out
    args = Args(file=env_file, allowed_keys=["APP_NAME"], filter_only=True)
    rc = handle_whitelist_command(args, out)
    assert rc == 0
    assert any("APP_NAME" in l for l in lines)
    assert not any("SECRET_KEY" in l for l in lines)


def test_filter_mode_shows_count(env_file, _out):
    lines, out = _out
    args = Args(file=env_file, allowed_keys=["PORT", "APP_NAME"], filter_only=True)
    rc = handle_whitelist_command(args, out)
    assert rc == 0
    assert any("2 allowed" in l for l in lines)
