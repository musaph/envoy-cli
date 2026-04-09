"""Unit tests for envoy.cli_template."""
import io
import pytest
from pathlib import Path
from types import SimpleNamespace

from envoy.cli_template import handle_template_command


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


def _args(**kwargs):
    defaults = {"template_cmd": None, "template_file": None, "vars": None, "output": None}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestHandleTemplateCommand:
    def test_no_subcommand_shows_usage(self):
        out = io.StringIO()
        rc = handle_template_command(_args(), out=out)
        assert rc == 1
        assert "Usage" in out.getvalue()

    def test_missing_template_file(self, tmp_dir):
        out = io.StringIO()
        rc = handle_template_command(
            _args(template_cmd="list-vars", template_file=str(tmp_dir / "nope.template")),
            out=out,
        )
        assert rc == 1
        assert "not found" in out.getvalue()

    def test_list_vars(self, tmp_dir):
        tpl = tmp_dir / "app.env.template"
        tpl.write_text("DB_PASS=${DB_PASSWORD}\nLOG=${LOG_LEVEL:-info}\n")
        out = io.StringIO()
        rc = handle_template_command(
            _args(template_cmd="list-vars", template_file=str(tpl)), out=out
        )
        assert rc == 0
        output = out.getvalue()
        assert "DB_PASSWORD" in output
        assert "required" in output
        assert "LOG_LEVEL" in output
        assert "optional" in output

    def test_render_to_stdout(self, tmp_dir):
        tpl = tmp_dir / "app.env.template"
        tpl.write_text("HOST=${HOST}\nPORT=${PORT:-5432}\n")
        vars_file = tmp_dir / "vars.env"
        vars_file.write_text("HOST=localhost\n")
        out = io.StringIO()
        rc = handle_template_command(
            _args(template_cmd="render", template_file=str(tpl), vars=str(vars_file)),
            out=out,
        )
        assert rc == 0
        assert "HOST=localhost" in out.getvalue()
        assert "PORT=5432" in out.getvalue()

    def test_render_to_file(self, tmp_dir):
        tpl = tmp_dir / "app.env.template"
        tpl.write_text("KEY=${KEY}\n")
        vars_file = tmp_dir / "vars.env"
        vars_file.write_text("KEY=myvalue\n")
        out_file = tmp_dir / "result.env"
        out = io.StringIO()
        rc = handle_template_command(
            _args(
                template_cmd="render",
                template_file=str(tpl),
                vars=str(vars_file),
                output=str(out_file),
            ),
            out=out,
        )
        assert rc == 0
        assert out_file.read_text() == "KEY=myvalue\n"

    def test_render_missing_required_variable(self, tmp_dir):
        tpl = tmp_dir / "app.env.template"
        tpl.write_text("SECRET=${SECRET_KEY}\n")
        out = io.StringIO()
        rc = handle_template_command(
            _args(template_cmd="render", template_file=str(tpl), vars=None),
            out=out,
        )
        assert rc == 1
        assert "SECRET_KEY" in out.getvalue()

    def test_render_missing_vars_file(self, tmp_dir):
        tpl = tmp_dir / "app.env.template"
        tpl.write_text("A=${A}\n")
        out = io.StringIO()
        rc = handle_template_command(
            _args(template_cmd="render", template_file=str(tpl), vars=str(tmp_dir / "nope.env")),
            out=out,
        )
        assert rc == 1
        assert "not found" in out.getvalue()
