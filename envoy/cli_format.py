"""CLI subcommands for env-format feature."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from envoy.env_format import EnvFormatter
from envoy.parser import EnvParser


def register_format_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("format", help="Format and normalize a .env file")
    sub = p.add_subparsers(dest="format_cmd")

    run_p = sub.add_parser("run", help="Apply formatting to a .env file")
    run_p.add_argument("file", help="Path to the .env file")
    run_p.add_argument("--no-uppercase", action="store_true", help="Do not uppercase keys")
    run_p.add_argument("--no-strip", action="store_true", help="Do not strip whitespace")
    run_p.add_argument("--quote", action="store_true", help="Quote all values")
    run_p.add_argument("--remove-empty", action="store_true", help="Remove empty values")
    run_p.add_argument("--in-place", action="store_true", help="Write changes back to file")


def handle_format_command(args: argparse.Namespace, out=print) -> int:
    if not hasattr(args, "format_cmd") or args.format_cmd is None:
        out("Usage: envoy format <subcommand>  (run)")
        return 1

    if args.format_cmd == "run":
        return _run_format(args, out)

    out(f"Unknown format subcommand: {args.format_cmd}")
    return 1


def _run_format(args: argparse.Namespace, out) -> int:
    path = Path(args.file)
    if not path.exists():
        out(f"Error: file not found: {path}")
        return 1

    parser = EnvParser()
    vars_ = parser.parse(path.read_text())

    formatter = EnvFormatter(
        uppercase_keys=not getattr(args, "no_uppercase", False),
        strip_values=not getattr(args, "no_strip", False),
        quote_values=getattr(args, "quote", False),
        remove_empty=getattr(args, "remove_empty", False),
    )

    result = formatter.format(vars_)

    if not result.has_changes and not result.skipped:
        out("No formatting changes needed.")
    else:
        for change in result.changes:
            out(f"  ~ {change.key}: {change.reason}")
        for key in result.skipped:
            out(f"  - {key}: removed (empty value)")

    if getattr(args, "in_place", False):
        from envoy.parser import EnvParser as _P
        serialized = _P().serialize(result.vars)
        path.write_text(serialized)
        out(f"Written to {path}")
    else:
        from envoy.parser import EnvParser as _P
        out(_P().serialize(result.vars))

    return 0
