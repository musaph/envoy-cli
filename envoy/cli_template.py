"""CLI sub-commands for env template rendering."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

from envoy.template import EnvTemplate
from envoy.parser import EnvParser


def register_template_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("template", help="Render .env templates")
    sub = p.add_subparsers(dest="template_cmd")

    render_p = sub.add_parser("render", help="Render a template file")
    render_p.add_argument("template_file", help="Path to the .env.template file")
    render_p.add_argument(
        "--vars",
        metavar="FILE",
        help="Optional .env file supplying substitution values",
    )
    render_p.add_argument("--output", "-o", metavar="FILE", help="Write output to file")

    list_p = sub.add_parser("list-vars", help="List variables in a template")
    list_p.add_argument("template_file", help="Path to the .env.template file")


def handle_template_command(args: argparse.Namespace, out=sys.stdout) -> int:
    if not getattr(args, "template_cmd", None):
        out.write("Usage: envoy template <render|list-vars>\n")
        return 1

    template_path = Path(args.template_file)
    if not template_path.exists():
        out.write(f"Error: template file not found: {template_path}\n")
        return 1

    raw = template_path.read_text()
    tmpl = EnvTemplate(raw)

    if args.template_cmd == "list-vars":
        for var in tmpl.variables():
            req = "required" if var.required else f"optional (default: {var.default!r})"
            out.write(f"  {var.name}  [{req}]\n")
        return 0

    # render
    context: Dict[str, str] = {}
    if getattr(args, "vars", None):
        vars_path = Path(args.vars)
        if not vars_path.exists():
            out.write(f"Error: vars file not found: {vars_path}\n")
            return 1
        context = EnvParser.parse(vars_path.read_text())

    missing = tmpl.missing_variables(context)
    if missing:
        out.write(f"Error: missing required variables: {missing}\n")
        return 1

    rendered = tmpl.render(context)
    if getattr(args, "output", None):
        Path(args.output).write_text(rendered)
        out.write(f"Written to {args.output}\n")
    else:
        out.write(rendered)
    return 0
