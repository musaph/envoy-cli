"""CLI subcommands for env inheritance."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Callable

from envoy.env_inherit import EnvInheritor
from envoy.parser import EnvParser


def register_inherit_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("inherit", help="Merge a base .env into a child .env")
    sub = p.add_subparsers(dest="inherit_cmd")

    run = sub.add_parser("run", help="Apply inheritance and print result")
    run.add_argument("base", help="Base .env file path")
    run.add_argument("child", help="Child .env file path")
    run.add_argument(
        "--no-empty-override",
        action="store_true",
        help="Child empty values do NOT override base values",
    )
    run.add_argument("--show-source", action="store_true", help="Show value source")


def handle_inherit_command(args: argparse.Namespace, out: Callable[[str], None] = print) -> int:
    if not hasattr(args, "inherit_cmd") or args.inherit_cmd is None:
        out("Usage: envoy inherit <subcommand>  (run)")
        return 1

    if args.inherit_cmd == "run":
        return _run(args, out)

    out(f"Unknown inherit subcommand: {args.inherit_cmd}")
    return 1


def _run(args: argparse.Namespace, out: Callable[[str], None]) -> int:
    base_path = Path(args.base)
    child_path = Path(args.child)

    if not base_path.exists():
        out(f"Error: base file not found: {base_path}")
        return 1
    if not child_path.exists():
        out(f"Error: child file not found: {child_path}")
        return 1

    parser = EnvParser()
    base_vars = parser.parse(base_path.read_text())
    child_vars = parser.parse(child_path.read_text())

    allow_empty = not getattr(args, "no_empty_override", False)
    inheritor = EnvInheritor(allow_empty_override=allow_empty)
    result = inheritor.inherit(base_vars, child_vars)

    for change in result.changes:
        if getattr(args, "show_source", False):
            out(f"{change.key}={change.final_value}  # [{change.source}]")
        else:
            out(f"{change.key}={change.final_value}")

    out(f"\n# Inherited {len(result.inherited_keys)} key(s) from base.")
    return 0
