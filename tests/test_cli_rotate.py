"""Tests for envoy.cli_rotate."""
import json
import os
import pytest
from unittest.mock import patch
from envoy.crypto import EnvoyCrypto
from envoy.cli_rotate import handle_rotate_command


def _encrypt(password: str, value: str) -> str:
    return EnvoyCrypto(password).encrypt(value)


@pytest.fixture
def tmp_storage(tmp_path):
    return tmp_path


def _args(env="test", storage_path=".", initiated_by="cli"):
    class Args:
        pass
    a = Args()
    a.env = env
    a.storage_path = storage_path
    a.initiated_by = initiated_by
    return a


class TestHandleRotateCommand:
    def test_no_env_shows_usage(self):
        class Args:
            env = None
        messages = []
        code = handle_rotate_command(Args(), out=messages.append)
        assert code == 1
        assert "Usage" in messages[0]

    def test_missing_storage_file_reports_error(self, tmp_storage):
        messages = []
        args = _args(env="missing", storage_path=str(tmp_storage))
        code = handle_rotate_command(args, out=messages.append)
        assert code == 1
        assert "no stored data" in messages[0]

    def test_successful_rotation(self, tmp_storage):
        old_pass = "old-pass"
        new_pass = "new-pass"
        blobs = {
            "SECRET": _encrypt(old_pass, "my-secret"),
        }
        blob_file = tmp_storage / "prod.json"
        blob_file.write_text(json.dumps(blobs))

        args = _args(env="prod", storage_path=str(tmp_storage))
        messages = []
        with patch("getpass.getpass", side_effect=[old_pass, new_pass, new_pass]):
            code = handle_rotate_command(args, out=messages.append)

        assert code == 0
        rotated = json.loads(blob_file.read_text())
        assert EnvoyCrypto(new_pass).decrypt(rotated["SECRET"]) == "my-secret"
        assert any("Rotation complete" in m for m in messages)

    def test_mismatched_new_passwords(self, tmp_storage):
        blobs = {"K": _encrypt("old", "v")}
        (tmp_storage / "env.json").write_text(json.dumps(blobs))
        args = _args(env="env", storage_path=str(tmp_storage))
        messages = []
        with patch("getpass.getpass", side_effect=["old", "new1", "new2"]):
            code = handle_rotate_command(args, out=messages.append)
        assert code == 1
        assert "do not match" in messages[0]

    def test_same_password_error(self, tmp_storage):
        blobs = {"K": _encrypt("pass", "v")}
        (tmp_storage / "env.json").write_text(json.dumps(blobs))
        args = _args(env="env", storage_path=str(tmp_storage))
        messages = []
        with patch("getpass.getpass", side_effect=["pass", "pass", "pass"]):
            code = handle_rotate_command(args, out=messages.append)
        assert code == 1
        assert "Error" in messages[0]
