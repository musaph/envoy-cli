import pytest
from types import SimpleNamespace
from envoy.cli_search import handle_search_command


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DATABASE_URL=postgres://localhost/db\n"
        "API_KEY=supersecret\n"
        "APP_ENV=staging\n"
        "DEBUG=true\n"
    )
    return str(p)


def _args(**kwargs):
    defaults = {"search_cmd": None, "file": None, "query": None,
                "keys_only": False, "case_sensitive": False}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestHandleSearchCommand:
    def test_no_subcommand_shows_usage(self, env_file):
        out = []
        rc = handle_search_command(_args(), out=out.append)
        assert rc == 1
        assert any("Usage" in line for line in out)

    def test_missing_file_returns_error(self):
        out = []
        rc = handle_search_command(
            _args(search_cmd="run", file="/nonexistent/.env", query="x"),
            out=out.append,
        )
        assert rc == 1
        assert any("not found" in line for line in out)

    def test_run_finds_match_in_key(self, env_file):
        out = []
        rc = handle_search_command(
            _args(search_cmd="run", file=env_file, query="API"),
            out=out.append,
        )
        assert rc == 0
        assert any("API_KEY" in line for line in out)

    def test_run_finds_match_in_value(self, env_file):
        out = []
        rc = handle_search_command(
            _args(search_cmd="run", file=env_file, query="postgres"),
            out=out.append,
        )
        assert rc == 0
        assert any("DATABASE_URL" in line for line in out)

    def test_run_no_match_reports_none(self, env_file):
        out = []
        rc = handle_search_command(
            _args(search_cmd="run", file=env_file, query="ZZZNOMATCH"),
            out=out.append,
        )
        assert rc == 0
        assert any("No matches" in line for line in out)

    def test_run_keys_only_skips_value_match(self, env_file):
        out = []
        rc = handle_search_command(
            _args(search_cmd="run", file=env_file, query="postgres", keys_only=True),
            out=out.append,
        )
        assert rc == 0
        assert any("No matches" in line for line in out)

    def test_prefix_filter(self, env_file):
        out = []
        rc = handle_search_command(
            _args(search_cmd="prefix", file=env_file, prefix="APP"),
            out=out.append,
        )
        assert rc == 0
        assert any("APP_ENV" in line for line in out)

    def test_prefix_no_match(self, env_file):
        out = []
        rc = handle_search_command(
            _args(search_cmd="prefix", file=env_file, prefix="XYZ"),
            out=out.append,
        )
        assert rc == 0
        assert any("No variables" in line for line in out)
