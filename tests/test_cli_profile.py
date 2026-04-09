"""Tests for envoy.cli_profile — CLI handlers for profile sub-commands."""

import io
import pytest
from argparse import Namespace
from unittest.mock import MagicMock

from envoy.cli_profile import handle_profile_command
from envoy.profile import Profile, ProfileManager


@pytest.fixture
def mock_config():
    store = {}

    cfg = MagicMock()
    cfg.get.side_effect = lambda k: store.get(k)
    cfg.set.side_effect = lambda k, v: store.update({k: v})
    return cfg


def _out():
    return io.StringIO()


class TestHandleProfileCommand:
    def test_no_subcommand_shows_usage(self, mock_config):
        args = Namespace(profile_command=None)
        buf = _out()
        code = handle_profile_command(args, mock_config, buf)
        assert code == 1
        assert "Usage" in buf.getvalue()

    def test_create_profile(self, mock_config):
        args = Namespace(profile_command="create", name="dev", description="Dev env", tags=[])
        buf = _out()
        code = handle_profile_command(args, mock_config, buf)
        assert code == 0
        assert "created" in buf.getvalue()

    def test_create_invalid_name(self, mock_config):
        args = Namespace(profile_command="create", name="123bad", description="", tags=[])
        buf = _out()
        code = handle_profile_command(args, mock_config, buf)
        assert code == 1
        assert "Error" in buf.getvalue()

    def test_create_duplicate_profile(self, mock_config):
        args = Namespace(profile_command="create", name="dev", description="", tags=[])
        buf = _out()
        handle_profile_command(args, mock_config, buf)
        buf2 = _out()
        code = handle_profile_command(args, mock_config, buf2)
        assert code == 1
        assert "Error" in buf2.getvalue()

    def test_list_empty(self, mock_config):
        args = Namespace(profile_command="list")
        buf = _out()
        code = handle_profile_command(args, mock_config, buf)
        assert code == 0
        assert "No profiles" in buf.getvalue()

    def test_list_with_profiles(self, mock_config):
        for name in ("dev", "prod"):
            create_args = Namespace(profile_command="create", name=name, description="", tags=[])
            handle_profile_command(create_args, mock_config, _out())

        buf = _out()
        code = handle_profile_command(Namespace(profile_command="list"), mock_config, buf)
        assert code == 0
        output = buf.getvalue()
        assert "dev" in output
        assert "prod" in output

    def test_show_existing_profile(self, mock_config):
        handle_profile_command(
            Namespace(profile_command="create", name="staging", description="Staging", tags=["infra"]),
            mock_config, _out()
        )
        buf = _out()
        code = handle_profile_command(Namespace(profile_command="show", name="staging"), mock_config, buf)
        assert code == 0
        assert "staging" in buf.getvalue()
        assert "Staging" in buf.getvalue()

    def test_show_missing_profile(self, mock_config):
        buf = _out()
        code = handle_profile_command(Namespace(profile_command="show", name="ghost"), mock_config, buf)
        assert code == 1
        assert "not found" in buf.getvalue()

    def test_delete_existing_profile(self, mock_config):
        handle_profile_command(
            Namespace(profile_command="create", name="dev", description="", tags=[]),
            mock_config, _out()
        )
        buf = _out()
        code = handle_profile_command(Namespace(profile_command="delete", name="dev"), mock_config, buf)
        assert code == 0
        assert "deleted" in buf.getvalue()

    def test_delete_missing_profile(self, mock_config):
        buf = _out()
        code = handle_profile_command(Namespace(profile_command="delete", name="ghost"), mock_config, buf)
        assert code == 1
        assert "not found" in buf.getvalue()

    def test_unknown_subcommand(self, mock_config):
        buf = _out()
        code = handle_profile_command(Namespace(profile_command="frobnicate"), mock_config, buf)
        assert code == 1
