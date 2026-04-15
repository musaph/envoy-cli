"""CLI subcommands for quoting/unquoting .env values."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from envoy.env_quote import EnvQuoter
from envoy.parser import EnvParser


def register_quote_subcommands(subparsers: Any) -> None:
    p = subparsers.add_parser("quote", help="Quote or unquote .env values")
    sub = p.add_subparsers(dest="quote_cmd")

    # -- quote ---------------------------------------------------------------
    q = sub.add_parser("add", help="Wrap values in quotes")
    q.add_argument("file", help="Path to .env file")
    q.add_argument(
        "--style",
        choices=["double", "single"],
        default="double",
        help="Quote character style (default: double)",
    )
    q.add_argument(
        "--only-if-needed",
        action="store_true",
        help="Only quote values that contain special characters",
    )
    q.add_argument(
        "--in-place", action="store_true", help="Overwrite the source file"
    )

    # -- unquote -------------------------------------------------------------
    u = sub.add_parser("remove", help="Strip quotes from values")
    u.add_argument("file", help="Path to .env file")
    u.add_argument(
        "--in-place", action="store_true", help="Overwrite the source file"
    )


def handle_quote_command(args: Any, out=print) -> int:
    if not hasattr(args, "quote_cmd") or args.quote_cmd is None:
        out("Usage: envoy quote <add|remove> <file>")
        return 1

    path = Path(args.file)
    if not path.exists():
        out(f"Error: file not found: {path}")
        return 1

    parser = EnvParser()
    try:
        vars_ = parser.parse(path.read_text())
    except Exception as exc:  # pragma: no cover
        out(f"Error: could not parse {path}: {exc}")
        return 1

    if args.quote_cmd == "add":
        style = getattr(args, "style", "double")
        only_if_needed = getattr(args, "only_if_needed", False)
        quoter = EnvQuoter(style=style, only_if_needed=only_if_needed)
        result = quoter.quote(vars_)
        action_label = "quoted"
    else:  # remove
        quoter = EnvQuoter()
        result = quoter.unquote(vars_)
        action_label = "unquoted"

    if not result.has_changes:
        out("No changes — all values already in the desired form.")
        return 0

    serialized = parser.serialize(result.vars)

    if getattr(args, "in_place", False):
        path.write_text(serialized)
        out(f"{action_label.capitalize()} {len(result.changes)} value(s) in {path}")
    else:
        out(serialized)
        out(
            f"# {len(result.changes)} value(s) would be {action_label}"
            " (use --in-place to apply)"
        )

    return 0
